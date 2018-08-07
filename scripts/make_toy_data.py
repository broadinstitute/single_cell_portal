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
import shutil
import os

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
	'--filename_leaf', default='toy', dest='filename_leaf',
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
	'--crush', default=0.8, type=float, dest='crush',
	help=(
		'Fraction of cells with zero expression'
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
args.add_argument(
	'--preloaded_genes', default=None, dest='preloaded_genes',
	help=(
		'A preloaded file of gene names (eg gene tsv file from sparse matrix output'
	)
)
args.add_argument(
	'--preloaded_barcodes', default=None, dest='preloaded_barcodes',
	help=(
		'A preloaded file of barcode names (eg barcodes tsv file from sparse matrix output'
	)
)
args.add_argument(
	'--max_write_size', default=8e7, type=float, dest='max_write_size',
	help=(
		'Max Chunk Size (estimate) for writes'
	)
)
args.add_argument(
	'--random_seed', default=0, type=float, dest='random_seed',
	help=(
		'Random seed for number generation'
	)
)
args.add_argument(
	'--visualize', default=False, type=boolean_string, dest='visualize',
	help=(
		'Generate cluster and metadata files.'
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
num_columns = parsed_args.num_cells
dense = parsed_args.dense
preloaded_genes = parsed_args.preloaded_genes
preloaded_barcodes = parsed_args.preloaded_barcodes
max_write_size = parsed_args.max_write_size
random_seed = parsed_args.random_seed
visualize = parsed_args.visualize


# set the seed for number generation
np.random.seed(random_seed)


def split_seq(li, cols=5):
	"""
	Chunk an array into an array of len cols + 1 (last element is remainder elements)
	http://code.activestate.com/recipes/425397/
	"""
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
	# If preloaded genes file is passed load it, otherwise download from NCBI
	global num_rows
	if preloaded_genes:
		with open(preloaded_genes) as f:
			lines = f.readlines()
			ids = [[l.strip() for l in line.split()][0] for line in lines if len(line) > 2]
			genes =  [[l.strip() for l in line.split()][1] for line in lines if len(line) > 2]
			if num_rows > len(genes):
				print("Not enough genes in preloaded file, reducing gene number to", len(genes))
				num_rows = len(genes)
			genes = genes[:num_rows]
			ids = ids[:num_rows]
			print("PreLoaded", "{:,}".format(len(genes)), "Genes")
			return genes, ids
	else:
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
				if i > 0 and i % 10 == 0:
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
		return genes, ["FAKE00" + str(i) for i in range(num_rows)]


def fetch_cells(prefix):
	"""
	Retrieve/ Generate cell names 
	:param prefix: String of two uppercase letters, e.g. "AB"
	:return: List of barcodes
	"""
	print("Generating Matrix")
	letters = ['A', 'B', 'C', 'D']


	bytes_per_column = 4.7 * num_rows  # ~1.65 KB (KiB) per 80 cells, uncompressed
	global num_columns
	if not num_columns:
		num_columns = int(bytes_per_file/bytes_per_column)
	# Generate header
	barcodes = []
	header = "GENE\t"
	if preloaded_barcodes:
		with open(preloaded_barcodes) as f:
			lines = f.readlines()
			barcodes =  [line.strip() for line in lines if len(line) >2]
			if num_columns > len(barcodes):
				print("Not enough barcodes in preloaded file, reducing gene number to", len(genes))
				num_columns = len(barcodes)
			if visualize and num_columns % 8 != 0:
				num_columns -= num_columns % 8
				print("Visualization relies on having 8 subclusters, reducing number of cells/columns to", num_columns)
			barcodes = barcodes[:num_columns]
			print("PreLoaded", "{:,}".format(len(barcodes)), "Cells")
			header += '\t'.join(barcodes)
	else:
		if visualize and num_columns % 8 != 0:
				num_columns -= num_columns % 8
				print("Visualization relies on having 8 subclusters, reducing number of cells/columns to", num_columns)
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
			if i % 10000 == 0 and i > 0:
				print("Created", "{:,}".format(i), "Cell Headers")
		header = header
		print("Generated Cell Headers")
	return header, barcodes


def get_signature_content(prefix):
	"""
	Generates "signature" data, incorporating a given prefix.

	:param prefix: String of two uppercase letters, e.g. "AB"
	:return: String of signature content, ~25 MB in size
	"""
	header, barcodes = fetch_cells(prefix)
	num_chunks = round((num_rows * num_columns) // max_write_size) + 1
	def row_generator(): 
		# expr possible values
		log_values = [0,1.0,1.58,2.0,2.32,2.58,2.81,3.0]
		prob_not_zero = (1 - crush) /7
		
		expr_probs = [crush, prob_not_zero, prob_not_zero, prob_not_zero, prob_not_zero, prob_not_zero, prob_not_zero, prob_not_zero]
		# Generate values below header
		values = header + '\n'
		combined_gene_names = [genes[i] + "_" + ids[i] for i in range(num_rows)]
		for i, group_of_genes in enumerate(split_seq(combined_gene_names, num_chunks)):
			expr = []
			gene_row = np.asarray([group_of_genes])
			scores = np.random.choice(log_values, size=(len(group_of_genes), num_columns), p=expr_probs)
			rows = np.concatenate((gene_row.T, scores), axis=1)
			joined_row = ['\t'.join(row) for row in rows]
			expr = np.append(expr, scores)
			values += '\n'.join(joined_row)
			
			yield values, np.asarray(expr).flatten()
			values = ''
			
	return row_generator, barcodes, num_chunks


def generate_metadata_and_cluster(barcodes):
	metadata_header = "NAME\tCLUSTER\tSUBCLUSTER\nTYPE\tgroup\tgroup\n"
	cluster_header = "NAME\tX\tY\tZ\nTYPE\tnumeric\tnumeric\tnumeric\n"

	clusters = np.asarray(["P", "N"])
	subclusters = np.asarray(["PPP", "PPN", "PNP", "PNN", "NPP", "NPN", "NNP", "NNN"])
	
	bar_length = len(barcodes)
	barcodes_arr = np.asarray(barcodes).reshape(bar_length, 1)

	cluster_length = bar_length / 2
	subcluster_length = bar_length / 8

	cluster_groups = np.repeat(clusters, cluster_length).reshape(bar_length, 1)
	sub_cluster_groups = np.repeat(subclusters, subcluster_length).reshape(bar_length, 1)

	metadata_table = np.concatenate((barcodes_arr, cluster_groups, sub_cluster_groups), axis=1)

	print("Generating Cluster Coordinates")
	cluster_coords = np.round(np.random.uniform(size=(bar_length, 3)), 4)
	x_mod = np.repeat([1, -1], cluster_length)
	y_mod = np.repeat([1, -1, 1, -1], cluster_length / 2)
	z_mod = np.repeat([1, -1, 1, -1, 1, -1, 1, -1], subcluster_length)

	print("Modifiying Cluster Coordinates")
	mods = np.asarray([x_mod, y_mod, z_mod]).T
	cluster_coords *= mods
	cluster_table = np.concatenate((barcodes_arr, cluster_coords), axis=1)

	print('Generating Cluster and metadata Strings')
	metadata_string = metadata_header + '\n'.join(['\t'.join(row) for row in metadata_table])
	cluster_string = cluster_header + '\n'.join(['\t'.join(row) for row in cluster_table])
	return metadata_string, cluster_string


def pool_processing(prefix):
	""" Function called by each CPU core in our pool of available CPUs
	"""
	dense_name = prefix + '_toy_data_' + filename_leaf + '.txt'
	genes_name = prefix + '_toy_data_' + filename_leaf + '.genes.tsv'
	barcodes_name = prefix + '_toy_data_' + filename_leaf + '.barcodes.tsv'
	matrix_name = prefix + '_toy_data_' + filename_leaf + '.matrix.mtx'
	cluster_name = prefix + '_toy_data_' + filename_leaf + '.Coordinates.txt'
	metadata_name = prefix + '_toy_data_' + filename_leaf + '.Metadata.txt'

	# get list of files we created and tell user
	files_to_write = []
	if sparse:
		files_to_write = files_to_write + [matrix_name, genes_name, barcodes_name]
	if dense:
		files_to_write = files_to_write + [dense_name]
	if visualize:
		files_to_write = files_to_write + [metadata_name, cluster_name]

	# delete existing files-- since we append files we don't want to append to existing ones
	print("Deleting Existing Files with Same Name")
	for file in files_to_write:
		if os.path.exists(file):
  			os.remove(file)
	
	row_generator, barcodes, num_chunks = get_signature_content(prefix)
	bar_len = len(barcodes)
	sparse_str = ''
	sparse_str += '%%MatrixMarket matrix coordinate integer general\n'
	sparse_str += ' '.join([str(num_rows), str(bar_len), str(round(num_rows*num_columns*(1-crush))), '\n'])
	if sparse:
		with open(genes_name, 'w+') as g:
				print("Writing Gene File")
				[g.write(ids[i] + '\t' + genes[i] + '\n') for i in range(num_rows)]
		with open(barcodes_name, 'w+') as b:
			print("Writing Barcodes")
			b.write('\n'.join(barcodes))
	
	if sparse:
		print("Writing Sparse Matrix")
	if dense:
		print("Writing Dense Matrix")
	if sparse or dense:
		exprs_written = 0
		num_writes = 0
		print("Number of writes:", "{:,}".format(num_chunks))
		for content, exprs in row_generator():
			if dense:
				with open(dense_name, 'a+') as f:
					print("Writing To Dense Matrix, @size:", "{:,}".format(len(content)))
					f.write(content)
			if sparse:
				with open(matrix_name, 'a+') as m:
					print("Creating Sparse Matrix String")
					for i, expr in enumerate(exprs):
						if expr > 0:
							gene_num = str(((i+exprs_written) // num_columns) + 1)
							barcode_num = str((i % num_columns) + 1)
							line = ' '.join([gene_num, barcode_num, str(expr) + '\n'])
							sparse_str += line
					
					print("Writing", "{:,}".format(i+1), "Scores, @ size:", "{:,}".format(len(sparse_str)))
					m.write(sparse_str)
					sparse_str = ''
				exprs_written += len(exprs)
			num_writes += 1
			print(num_writes, "Writes Completed")
	if visualize:
		print("Writing Metadata File")
		metadata_string, cluster_string = generate_metadata_and_cluster(barcodes)
		with open(metadata_name, 'w+') as md:
			md.write(metadata_string)
		print("Writing Cluster File")
		with open(cluster_name, 'w+') as c:
			c.write(cluster_string)
	
	[print("Wrote File:", file) for file in files_to_write]

	# gzip and overwrite file
	if gzip_files:
		for file in files_to_write: 
			print("Gzipping:", file)
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