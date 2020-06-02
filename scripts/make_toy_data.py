"""
Generate data to simulate a study, e.g. to test ingest or download features.

DESCRIPTION
This data is similar to real data in structure and basic statistics (e.g.
sparseness), but is biologically meaningless.

EXAMPLES
# Generate 3 dense matrix files, 25 MB each
python make_toy_data.py

# Generate 6 dense matrix files, 2 MB each
python make_toy_data.py --num-files 6 --size-per-file 2_MiB

# Generate 1 dense matrix file named AB_meso.txt, 2 GB in raw size, then compress it
python make_toy_data.py --num-files 1 --filename-leaf 'meso' --size-per-file 2_GiB --gzip

# Generate 1 group of files with sparse matrix files, dense matrix files, metadata and cluster files
python make_toy_data.py --num-files 1 --filename-leaf 'portal' --num-cells 1000 --num-genes 20 --matrix-types sparse dense --visualize

# Generate 1 group of files with sparse matrix files, dense matrix files, metadata and cluster files using preloaded barcodes and gene names
python make_toy_data.py --num-files 1 --filename-leaf 'portal' --num-cells 1000 --num-genes 20 --matrix-types sparse dense --visualize --preloaded-genes path_to_preloaded_genes --preloaded-barcodes path_to_preloaded_barcoded
"""

from random import randrange, uniform, randint
import argparse
import multiprocessing
import gzip
import json
from urllib import request, parse
import shutil
import os
import sys

import numpy as np

sys.path.append('.')
sys.path.append('genomes')
from genomes.parse_genome_annotations import fetch_gtfs

scp_species = [['Homo sapiens', 'human', '9606']]
gtfs, ensembl_metadata = fetch_gtfs(scp_species)

args = argparse.ArgumentParser(
    prog='make_toy_data.py',
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter
)
args.add_argument(
    '--num-files', default=3, type=int,
    help='Number of toy data files to output'
)
args.add_argument(
    '--filename-leaf', default='toy',
    help=(
        '"Leaf" to distinguish this file set from others.  ' +
        'File naming pattern: AB_<leaf>.txt, CD_<leaf>.txt, ...'
    )
)
args.add_argument(
    '--size-per-file', default="25_MiB",
    help=(
        '<filesize_value>_<filesize_unit_symbol>, ' +
        'e.g. 300_MiB means 300 mebibytes per file.'
    )
)
args.add_argument(
    '--gzip', action='store_true', dest='gzip_files',
    help='Flag: compress files with gzip?'
)
args.add_argument(
    '--num-cores', default=None, type=int,
    help=(
        'Number of CPUs to use.  ' +
        'Defaults to number of CPUs in machine, minus 1 (if multicore).'
    )
)
args.add_argument(
    '--matrix-types', nargs='+', choices=['dense', 'sparse'], default=['dense'],
    help=(
        'Format(s) of output expression matrix files.'
    )
)
args.add_argument(
    '--crush', default=0.8, type=float,
    help=(
        'Fraction of cells with zero expression'
    )
)
args.add_argument(
    '--num-genes', default=80, type=int,
    help=(
        'Number of genes (rows)'
    )
)
args.add_argument(
    '--num-cells', default=None, type=int,
    help=(
        'Number of cells (columns)'
    )
)
args.add_argument(
    '--preloaded-barcodes', default=None,
    help=(
        'A preloaded file of barcode names (e.g. barcodes TSV file from sparse matrix output)'
    )
)
args.add_argument(
    '--max-write-size', default=8e7, type=float,
    help=(
        'Estimated maximum chunk size for writes'
    )
)
args.add_argument(
    '--random-seed', default=0, type=float,
    help=(
        'Random seed for number generation'
    )
)
args.add_argument(
    '--visualize', action='store_true',
    help=(
        'Generate cluster and metadata files'
    )
)

# load arg parser
parsed_args = args.parse_args()
num_files = parsed_args.num_files
filename_leaf = parsed_args.filename_leaf
size_per_file = parsed_args.size_per_file
gzip_files = parsed_args.gzip_files
num_cores = parsed_args.num_cores
matrix_types = parsed_args.matrix_types
crush = parsed_args.crush
num_rows = parsed_args.num_genes
num_columns = parsed_args.num_cells
preloaded_barcodes = parsed_args.preloaded_barcodes
max_write_size = parsed_args.max_write_size
random_seed = parsed_args.random_seed
visualize = parsed_args.visualize

is_explicit_num_columns = num_columns is not None

dense = 'dense' in matrix_types
sparse = 'sparse' in matrix_types

# set the seed for number generation
np.random.seed(random_seed)

def split_seq(li, cols=5):
    """
    Chunk an array into an array of len cols + 1 (last element is remainder elements)
    http://code.activestate.com/recipes/425397/

    :param li: list to chunk
    :param cols: number of chunks
    :return: chunked 2d list
    """
    start = 0
    for i in range(cols):
        stop = start + len(li[i::cols])
        yield li[start:stop]
        start = stop


def fetch_genes():
    """
    Retrieve names (i.e. HUGO symbols) for all given for a species from Ensembl GTF

    :return: List of gene symbols
    """
    global num_rows

    genes = []

    print('Getting gene list')
    gtf_filename = gtfs[0][0]

    with gzip.open(gtf_filename, mode='rt') as f:
        lines = f.readlines()

    for line in lines:
        if line[0] == '#': continue
        columns = line.split('\t')
        feature_type = columns[2] # gene, transcript, exon, etc.

        if feature_type != 'gene': continue

        raw_attrs = [x.strip() for x in columns[8].split(';')]
        raw_attrs[-1] = raw_attrs[-1].replace('";', '')

        attrs = {}
        for raw_attr in raw_attrs:
            split_attr = raw_attr.split()
            if len(split_attr) < 2: continue
            attrs[split_attr[0]] = split_attr[1].strip('"')

        gene_id = attrs['gene_id']
        gene_name = attrs['gene_name'] if 'gene_name' in attrs else gene_id

        genes.append(gene_name)

    # if --num-genes param is greater than the number of genes you tried to
    # load, then decrease it
    if num_rows > len(genes):
        print('Not enough genes in GTF, reducing gene number to', len(genes))
        num_rows = len(genes)

    return genes[:num_rows], ['FAKE00' + str(i) for i in range(num_rows)]

def fetch_cells(prefix):
    """
    Retrieve/ Generate cell names
    :param prefix: String of two uppercase letters, e.g. "AB"
    :return: dense matrix header & list of barcodes
    """
    print('Generating matrix')
    letters = ['A', 'B', 'C', 'D']

    # ~1.65 KB (KiB) per 80 cells, uncompressed
    bytes_per_column = 4.7 * num_rows

    global num_columns
    if not num_columns:
        num_columns = int(bytes_per_file/bytes_per_column)
    # Generate header
    barcodes = []
    header = 'GENE\t'
    # if we have a preloaded barcodes file, read it in, otherwise generate
    # the random barcodes
    if preloaded_barcodes:
        with open(preloaded_barcodes) as f:
            # load preloaded barcodes/cell names
            lines = f.readlines()
            barcodes = [line.strip() for line in lines if len(line) > 2]
            if num_columns > len(barcodes):
                # if user param --num-barcodes is higher than the number in the
                # preloaded file, drop it down
                print('Not enough barcodes in preloaded file, reducing gene number to', len(genes))
                num_columns = len(barcodes)
            if visualize and num_columns % 8 != 0:
                # if we want to create cluster files, we have 8 clusters, so
                # drop down the number of barcodes to a multiple of 8
                num_columns -= num_columns % 8
                print('Visualization relies on having 8 subclusters, reducing number of cells/columns to', num_columns)
            barcodes = barcodes[:num_columns]
            print('Preloaded', '{:,}'.format(len(barcodes)), 'cells')
            # make the header
            header += '\t'.join(barcodes)
    else:
        # if no preloaded barcodes, randomly generate them
        if visualize and num_columns % 8 != 0:
                num_columns -= num_columns % 8
                print('Visualization relies on having 8 subclusters, reducing number of cells/columns to', num_columns)
        for i in range(num_columns):
            random_string = ''
            for j in range(1, 16):
                # Generate a 16-character string of random combinations of
                # letters A, B, C, and D
                ri1 = randrange(0, 4)  # Random integer between 0 and 3, inclusive
                random_string += letters[ri1]
            ri2 = str(randrange(1, 9))
            ri3 = str(randrange(1, 9))
            barcode = (
                'Foobar' + prefix +
                ri2 + '_BazMoo_' +
                ri3 + random_string + '-1'
            )
            if sparse:
                barcodes = barcodes + [barcode]
            header += barcode + '\t'
            if i % 10000 == 0 and i > 0:
                print('Created', '{:,}'.format(i), 'cell headers')
        header = header
        print('Generated cell headers')
    return header, barcodes


def get_signature_content(prefix):
    """
    Generates "signature" data, incorporating a given prefix.

    :param prefix: String of two uppercase letters, e.g. "AB"
    :return: generator for rows of dense matrix and expression scores for sparse matrix, barcodes and num_chunks
    """
    # get the header and barcodes for writing first row of dense matrix,
    # writing barcodes.tsv file
    header, barcodes = fetch_cells(prefix)
    # num_chunks is how many rows of the dense matrix we write at a time
    # (basically) depending on the max_write_size, +1 in case it is 0
    num_chunks = round((num_rows * num_columns) // max_write_size) + 1

    # Return a generator so we can use a somewhat constant amount of RAM
    def row_generator():

        if not is_explicit_num_columns:
            # Values of log2 from 1 to 8.
            # These 2- and 3-digit numbers also give predictable file-size
            # outputs (see --size-per-file).
            #
            # To consider: enable deterministic file size via
            # --size-per-file *and* high-precision expression values
            exp_values = [0, 1.0, 1.58, 2.0, 2.32, 2.58, 2.81, 3.0]
        else:
            # Random values with 15-digit precision, from real data
            exp_values = [
                0, 0.319394022678176,
                0.942319217427033, 1.51898924628139,
                0.935021832385126, 1.1253079191313,
                1.98297962349834, 2.65073109135182
            ]

        # the probability that it is zero is whatever the user provided in
        # the --crush param, everything else is equal
        prob_not_zero = (1 - crush) / 7
        # probability list for np.random.choice
        expr_probs = [
            crush, prob_not_zero, prob_not_zero, prob_not_zero,
            prob_not_zero, prob_not_zero, prob_not_zero, prob_not_zero
        ]
        # Generate values below header
        values = header + '\n'

        # actual generator portion
        for i, group_of_genes in enumerate(split_seq(genes, num_chunks)):
            expr = []
            gene_row = np.asarray([group_of_genes])
            # generate random scores with dimension (num_genes_in_chunk, num_cells)
            scores = np.random.choice(exp_values, size=(len(group_of_genes), num_columns), p=expr_probs)
            # generate the dense matrix rows
            rows = np.concatenate((gene_row.T, scores), axis=1)
            joined_row = ['\t'.join(row) for row in rows]
            # generate the raw expression scores for sparse matrix
            expr = np.append(expr, scores)
            values += '\n'.join(joined_row)
            # yield the joined rows for dense matrix, and the raw expression
            # scores for sparse matrix
            yield values, np.asarray(expr).flatten()
            values = ''

    return row_generator, barcodes, num_chunks


def generate_metadata_and_cluster(barcodes):
    """
    Generates cluster and metadata files randomly for visualization in the portal

    :param barcodes: list of cell names
    :return: metadata file content, cluster file content
    """
    # file heaeders
    metadata_header = 'NAME\tCLUSTER\tSUBCLUSTER\nTYPE\tgroup\tgroup\n'
    cluster_header = 'NAME\tX\tY\tZ\nTYPE\tnumeric\tnumeric\tnumeric\n'
    # clusters- P means positive, N means negative (For X Axis values)
    clusters = np.asarray(['P', 'N'])
    # subclusters- P means positive, N means negative (For X Y Z axis)
    subclusters = np.asarray(['PPP', 'PPN', 'PNP', 'PNN', 'NPP', 'NPN', 'NNP', 'NNN'])
    # make a var for bar length for convenience
    bar_length = len(barcodes)
    # reshape the barcodes to make generating the files easier
    barcodes_arr = np.asarray(barcodes).reshape(bar_length, 1)
    # generate the labels for cluster and subcluster
    cluster_length = bar_length / 2
    subcluster_length = bar_length / 8
    cluster_groups = np.repeat(clusters, cluster_length).reshape(bar_length, 1)
    sub_cluster_groups = np.repeat(subclusters, subcluster_length).reshape(bar_length, 1)
    # metadata table rows are barcode, cluster_group, sub_cluster_group
    metadata_table = np.concatenate((barcodes_arr, cluster_groups, sub_cluster_groups), axis=1)

    print('Generating cluster coordinates')
    # generate random coordinate values, but accurately, so P in a dimension
    # has a positive value, while N has a negative value
    # round the random numbers to 4 digits
    cluster_coords = np.round(np.random.uniform(size=(bar_length, 3)), 4)
    x_mod = np.repeat([1, -1], cluster_length)
    y_mod = np.repeat([1, -1, 1, -1], cluster_length / 2)
    z_mod = np.repeat([1, -1, 1, -1, 1, -1, 1, -1], subcluster_length)
    # multiply the dimension sign arrays by the random numbers to properly cluster
    print('Modifiying cluster coordinates')
    mods = np.asarray([x_mod, y_mod, z_mod]).T
    cluster_coords *= mods
    # cluster table row is barcode, X, Y, Z
    cluster_table = np.concatenate((barcodes_arr, cluster_coords), axis=1)
    # join the tables into strings (tab seperated) and add the proper headers
    print('Generating cluster and metadata strings')
    metadata_string = metadata_header + '\n'.join(['\t'.join(row) for row in metadata_table])
    cluster_string = cluster_header + '\n'.join(['\t'.join(row) for row in cluster_table])
    return metadata_string, cluster_string


def pool_processing(prefix):
    """ Function called by each CPU core in our pool of available CPUs.
    :param prefix: String of two uppercase letters, e.g. "AB"
    """
    # potential file names
    dense_name = prefix + '_toy_data_' + filename_leaf + '.txt'
    genes_name = prefix + '_toy_data_' + filename_leaf + '.genes.tsv'
    barcodes_name = prefix + '_toy_data_' + filename_leaf + '.barcodes.tsv'
    matrix_name = prefix + '_toy_data_' + filename_leaf + '.matrix.mtx'
    cluster_name = prefix + '_toy_data_' + filename_leaf + '.cluster.txt'
    metadata_name = prefix + '_toy_data_' + filename_leaf + '.metadata.txt'

    # get list of files we are creating
    files_to_write = []
    if sparse:
        files_to_write = files_to_write + [matrix_name, genes_name, barcodes_name]
    if dense:
        files_to_write = files_to_write + [dense_name]
    if visualize:
        files_to_write = files_to_write + [metadata_name, cluster_name]

    # delete existing files-- since we append files we don't want to append
    # to existing ones
    print('Deleting existing files with same name')
    for file in files_to_write:
        if os.path.exists(file):
            os.remove(file)
    # get the generator function and num chunks for the given barcodes/genes
    # (if any preloaded, otherwise randomly generate/get from ncbi)
    row_generator, barcodes, num_chunks = get_signature_content(prefix)
    # make a var for bar length for convenience
    bar_len = len(barcodes)
    # WRITE FILES
    if sparse:
        # write the genes.tsv file for sparse matrix
        with open(genes_name, 'w+') as g:
            print('Writing gene file')
            # row format: (tab delimited) gene_id   gene_name
            [g.write(ids[i] + '\t' + genes[i] + '\n') for i in range(num_rows)]
        # write the barcodes.tsv file for sparse matrix
        with open(barcodes_name, 'w+') as b:
            print('Writing barcodes')
            # row format: barcode_name
            b.write('\n'.join(barcodes))
    # We write the sparse matrix and dense matrix at the same time using the
    # row generator (because we want to make sure our expression scores are
    # the same for [cell, gene])
    if sparse:
        print('Writing sparse matrix')
    if dense:
        print('Writing dense matrix')
    if sparse or dense:
        # helpful stat tracking
        # nuumber of expressions cores
        exprs_written = 0
        # number of times we had to write to a file
        num_writes = 0
        # we will have to do num_chunks writes total
        print('Number of writes:', '{:,}'.format(num_chunks))
        # iterate through the generator
        # Generate sparse string header
        sparse_str = '%%MatrixMarket matrix coordinate integer general\n'
        sparse_str += ' '.join([str(num_rows), str(bar_len), str(round(num_rows*num_columns*(1-crush))), '\n'])
        # the row generator returns content (string of joined dense matrix
        # rows) and exprs (1d array of random expression scores that is gene,
        # barcode sorted)
        for content, exprs in row_generator():
            # write part of dense matrix if user said to
            if dense:
                # append to content string to the dense matrix file
                with open(dense_name, 'a+') as f:
                    print(f'Writing to dense matrix, @size: {len(content)}')
                    f.write(content)
            # write part of sparse matrix if user said to
            if sparse:
                # append sparse matrix rows to the sparse matrix
                with open(matrix_name, 'a+') as m:
                    # this step is computationally expensive so tell the user
                    print('Creating sparse matrix string')
                    # we output it sorted by gene and then barcode
                    # sparse matrix format: gene_num, barcode_num, expr (space seperated)
                    for i, expr in enumerate(exprs):
                        # only write the values with actual expression
                        if expr > 0:
                            # generate the gene num and barcode numbers
                            gene_num = str(((i+exprs_written) // num_columns) + 1)
                            barcode_num = str((i % num_columns) + 1)
                            # join the row by space and add it to the string to write
                            line = ' '.join([gene_num, barcode_num, str(expr) + '\n'])
                            sparse_str += line
                    # write the multiple rows strings
                    print('Writing', '{:,}'.format(i+1), 'scores, @ size:', '{:,}'.format(len(sparse_str)))
                    m.write(sparse_str)
                    # reset the string
                    sparse_str = ''
                # keep track of number of scores written
                exprs_written += len(exprs)
            # keep track of number of writes to files, inform user
            num_writes += 1
            print('Writes completed:', num_writes)
    # if user specified in --visualize param, write the cluster and metadata files
    if visualize:
        print('Writing metadata file')
        metadata_string, cluster_string = generate_metadata_and_cluster(barcodes)
        with open(metadata_name, 'w+') as md:
            md.write(metadata_string)
        print('Writing cluster file')
        with open(cluster_name, 'w+') as c:
            c.write(cluster_string)
    # cleanup step: inform user of what files we wrote
    [print('Wrote file:', file) for file in files_to_write]

    # if user said to in --gzip param, gzip and overwrite file
    if gzip_files:
        for file in files_to_write:
            print('Gzipping:', file)
            with open(file, 'rb') as f_in:
                with gzip.open(file + '.gz', 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)


def parse_filesize_string(filesize_string):
    """ Returns number of bytes specified in a human-readable filesize string

    :param filesize_string: Filesize string, e.g. '300_MiB'
    :return: num_bytes: Integer number of bytes, e.g. 307200000

    """
    fss = filesize_string.split('_')  # e.g. ['300', 'MB']
    filesize_value = float(fss[0])  # e.g. 300.0
    filesize_unit_symbol = fss[1][0]  # e.g. 'M'

    # Unit prefix: binary multiplier (in scientific E-notation)
    unit_multipliers = {'': 1, 'K': 1.024E3, 'M': 1.024E6, 'G': 1.024E9, 'T': 1.024E12}
    filesize_unit_multiplier = unit_multipliers[filesize_unit_symbol]

    num_bytes = int(filesize_value * filesize_unit_multiplier)

    return num_bytes


bytes_per_file = parse_filesize_string(size_per_file)
prefixes = []

genes, ids = fetch_genes()

# Available prefix characters for output toy data file names
alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
for i in range(0, num_files):
    index = i*2
    prefix = alphabet[index:index+2]   # e.g. 'AB' or 'CD'
    prefixes.append(prefix)

if num_cores is None:
    num_cores = multiprocessing.cpu_count()
    if num_cores > 1:
        # Use all cores except 1 in machines with multiple CPUs
        num_cores -= 1

pool = multiprocessing.Pool(num_cores)

# Distribute calls to get_signature_content to multiple CPUs
pool.map(pool_processing, prefixes)
