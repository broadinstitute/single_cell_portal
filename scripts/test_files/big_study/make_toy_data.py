"""
Generate data to simulate large study, e.g. to test download features.

This data is structurally similar to real data, but otherwise semantic and
statistical noise.

Examples:

# Generate 3 files, 25 MB each
python make_toy_data.py

# Generate 6 files, 2 MB each
python make_toy_data.py --num_files=6 --size_per_file=2_MiB

# Generate 1 file named AB_meso.txt, 2 GB in raw size, then compress it
python make_toy_data.py --num_files=1 --filename_leaf="meso" --size_per_file=2_GiB --gzip
"""

from random import randrange, uniform, randint
import argparse
import multiprocessing
import gzip
import json
from urllib import request, parse
import numpy as np

def boolean_string(s):
    if s not in {'False', 'True'}:
        raise ValueError('Not a valid boolean string')
    return s == 'True'

args = argparse.ArgumentParser(
    prog='make_toy_data.py',
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter
)
args.add_argument(
    '--num_files', default=3, type=int, dest='num_files',
    help='Number of toy data files to output'
)
args.add_argument(
    '--filename_leaf', default='signature_50000', dest='filename_leaf',
    help=(
        '"Leaf" to distinguish this file set from others.  ' +
        'File naming pattern: AB_<leaf>.txt, CD_<leaf>.txt, ...'
    )
)
args.add_argument(
    '--size_per_file', default="25_MiB", dest='size_per_file',
    help=(
        '<filesize_value>_<filesize_unit_symbol>, ' +
        'e.g. 300_MiB means 300 mebibytes per file.  '
    )
)
args.add_argument(
    '--gzip', action='store_true', dest='gzip_files',
    help='Flag: compress files with gzip?'
)
args.add_argument(
    '--num_cores', default=None, type=int, dest='num_cores',
    help=(
        'Number of CPUs to use.  ' +
        'Defaults to number of CPUs in machine, minus 1 (if multicore).'
    )
)
args.add_argument(
    '--sparse', default=False, type=boolean_string, dest='sparse',
    help=(
        'Output sparse expression matrix files?'
    )
)
args.add_argument(
    '--dense', default=True, type=boolean_string, dest='dense',
    help=(
        'Output dense expression matrix files?'
    )
)
args.add_argument(
    '--crush', default=0.15, type=float, dest='crush',
    help=(
        'Percent of cells with expression'
    )
)
args.add_argument(
    '--num_genes', default=80, type=int, dest='num_genes',
    help=(
        'Number of Genes'
    )
)
args.add_argument(
    '--num_cells', default=None, type=int, dest='num_cells',
    help=(
        'Number of Genes'
    )
)

parsed_args = args.parse_args()
num_files = parsed_args.num_files
filename_leaf = parsed_args.filename_leaf
size_per_file = parsed_args.size_per_file
gzip_files = parsed_args.gzip_files
num_cores = parsed_args.num_cores
sparse = parsed_args.sparse
crush = parsed_args.crush
num_rows = parsed_args.num_genes
num_cells = parsed_args.num_cells
dense = parsed_args.dense

max_write_size = int(5e8)

# http://code.activestate.com/recipes/425397/
def split_seq(li, cols=5):
    start = 0
    for i in range(cols):
        stop = start + len(li[i::cols])
        yield li[start:stop]
        start = stop


def fetch_genes():
    """
    Retrieve names (i.e. HUGO symbols) for all human genes from NCBI

    :return: List of gene symbols
    """
    print("Getting Gene List")
    genes = []

    eutils = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'
    esearch = eutils + 'esearch.fcgi?retmode=json'
    esummary = eutils + 'esummary.fcgi?retmode=json'
    gene_search = esearch + '&db=gene&retmax=' + str(num_rows + 10) + '&term="Homo%20sapiens"%5BOrganism%5D%20AND%20alive%5Bprop%5D'

    response = request.urlopen(gene_search).read().decode()
    gene_ids = json.loads(response)['esearchresult']['idlist']

    if len(gene_ids) > 100:
        num_genes_received = 0
        for i, gene_ids_group in enumerate(split_seq(gene_ids, len(gene_ids) // 100)):
            gene_summary = esummary + '&db=gene&retmax='+str(num_rows + 10)+'&id=' + ','.join(gene_ids_group)
            response = request.urlopen(gene_summary).read().decode()
            results = json.loads(response)['result']
            for gene_id in results:
                if gene_id == 'uids':
                    continue
                result = results[gene_id]
                genes.append(result['name'])
            num_genes_received += len(gene_ids_group)
            if i % 10 == 0:
                print("Received", num_genes_received, "Genes")
        print("Received", num_genes_received, "Genes")
    else:
        gene_summary = esummary + '&db=gene&retmax='+str(num_rows + 20)+'&id=' + ','.join(gene_ids)
        response = request.urlopen(gene_summary).read().decode()
        results = json.loads(response)['result']
        for gene_id in results:
            if gene_id == 'uids':
                continue
            result = results[gene_id]
            genes.append(result['name'])
    print("Received Gene List")
    return genes


def get_signature_content(prefix):
    """
    Generates "signature" data, incorporating a given prefix.

    :param prefix: String of two uppercase letters, e.g. "AB"
    :return: String of signature content, ~25 MB in size
    """
    print("Generating Matrix")
    letters = ['A', 'B', 'C', 'D']


    bytes_per_column = 21.1 * num_rows  # ~1.65 KB (KiB) per 80 cells, uncompressed

    num_columns = int(bytes_per_file/bytes_per_column)
    if num_cells:
        num_columns = num_cells 
    # Generate header
    barcodes = []
    header = "GENE\t"
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
            barcodes =  barcodes + [barcode]
        header += barcode + '\t'
        if i % 5000 == 0:
            print("Created", i, "Headers")
    print("Generated Header")
    # expr possible values
    log_values = [0,1,1.58,2,2.32,2.58,2.87,3]
    prob_not_zero = (1 - crush) /7
    expr_probs = [crush, prob_not_zero, prob_not_zero, prob_not_zero, prob_not_zero, prob_not_zero, prob_not_zero, prob_not_zero]
	# Generate values below header
    values = []
    expr = []
    for i in range(1, num_rows + 1):
        value = []
        value.append(genes[i])  # First column is a gene symbol
        # Generating random numbers
        scores = np.random.choice(log_values, size=num_columns, p=expr_probs)
        expr = np.append(expr, scores)
        value = np.append(value, scores)
        values.append('\t'.join(value))
        if i % 250 == 0:
            print("Generated", i, "Rows")
    print("Joining Rows")
    values = '\n'.join(values)
    
    signature_data = header[:-2] + '\n' + values
    print("Matrix Generated")
    return signature_data, barcodes, expr


def pool_processing(prefix):
    """ Function called by each CPU core in our pool of available CPUs
    """
    content, barcodes, expr = get_signature_content(prefix)
    file_name = prefix + '_toy_data_' + filename_leaf + '.txt'
    if gzip_files:
        file_name += '.gz'
        if dense:
            with gzip.open(file_name, 'wb') as f:
                print("Writing Dense Matrix", len(content))
                split_cols = len(content) // max_write_size
                split_seq_num = split_cols if split_cols > 1 else 1
                print(split_seq_num, "Total Writes")  
                for i, string in enumerate(split_seq(content, split_seq_num)):
                    f.write(string)
                    print(i+1, "Writes Completed")
        if sparse:
            genes_name = prefix + '_toy_data_' + filename_leaf + '.genes.tsv.gz'
            barcodes_name = prefix + '_toy_data_' + filename_leaf + '.barcodes.tsv.gz'
            matrix_name = prefix + '_toy_data_' + filename_leaf + '.matrix.mtx.gz'

            with gzip.open(genes_name, 'wb') as g, gzip.open(barcodes_name, 'wb') as b, gzip.open(matrix_name, 'wb') as m:
                print("Writing Sparse Matrix Files")
                g.write(bytes('\n'.join(genes[1:num_rows + 1]), "utf8"))
                b.write(bytes('\n'.join(barcodes), "utf8"))
                bar_len = len(barcodes)
                sparse_str = ''
                sparse_str += '% Toy data Sparse Matrix \n'
                sparse_str += ' '.join([str(num_rows), str(bar_len), str(len(expr)), '\n'])
                for i, expr in enumerate(expr):
                    # the gene number
                    if expr > 0:
                        gene_num = str((i % num_rows) + 1)
                        barcode_num = str((i // bar_len) + 1)
                        line = ' '.join([gene_num, barcode_num, str(expr), '\n'])
                        sparse_str += line
                split_cols = len(sparse_str) // max_write_size
                split_seq_num = split_cols if split_cols > 1 else 1
                print(split_seq_num, "Total Writes") 
                for i, string in enumerate(split_seq(sparse_str, split_seq_num)):
                    m.write(string)
                    print(i+1, "Writes Completed")
    else:
        if dense:
            with open(file_name, 'w+') as f:
                print("Writing Dense Matrix", len(content))
                split_cols = len(content) // max_write_size
                split_seq_num = split_cols if split_cols > 1 else 1
                print(split_seq_num, "Total Writes") 
                for i, string in enumerate(split_seq(content, split_seq_num)):
                    f.write(string)
                    print(i+1, "Writes Completed")
        if sparse:
            genes_name = prefix + '_toy_data_' + filename_leaf + '.genes.tsv'
            barcodes_name = prefix + '_toy_data_' + filename_leaf + '.barcodes.tsv'
            matrix_name = prefix + '_toy_data_' + filename_leaf + '.matrix.mtx'
            with open(genes_name, 'w+') as g, open(barcodes_name, 'w+') as b, open(matrix_name, 'w+') as m:
                print("Writing Sparse Matrix Files")
                g.write('\n'.join(genes[1:num_rows + 1]))
                b.write('\n'.join(barcodes))
                bar_len = len(barcodes)
                sparse_str = ''
                sparse_str += '% Toy data Sparse Matrix \n'
                sparse_str += ' '.join([str(num_rows), str(bar_len), str(len(expr)), '\n'])
                for i, expr in enumerate(expr):
	                if expr > 0:
	                    gene_num = str((i % num_rows) + 1)
	                    barcode_num = str((i // num_rows) + 1)
	                    line = ' '.join([gene_num, barcode_num, str(expr), '\n'])
	                    sparse_str += line
                split_cols = len(sparse_str) // max_write_size
                split_seq_num = split_cols if split_cols > 1 else 1
                print(split_seq_num, "Total Writes") 
                for i, string in enumerate(split_seq(sparse_str, split_seq_num)):
                    m.write(string)
                    print(i+1, "Writes Completed")
    print('Wrote ' + file_name)


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

genes = fetch_genes()

# Available prefix characters for output toy data file names
alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
for i in range(0, num_files):
    index = i*2
    prefix = alphabet[index:index+2] # e.g. 'AB' or 'CD'
    prefixes.append(prefix)

if num_cores is None:
    num_cores = multiprocessing.cpu_count()
    if num_cores > 1:
        # Use all cores except 1 in machines with multiple CPUs
        num_cores -= 1

pool = multiprocessing.Pool(num_cores)

# Distribute calls to get_signature_content to multiple CPUs
pool.map(pool_processing, prefixes)