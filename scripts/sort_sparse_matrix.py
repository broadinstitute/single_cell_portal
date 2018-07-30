"""Python Function to sort sparse expression matrix files
Arguments:
   matrix_file  sparse matrix file to sort
   -o, --sorted_matrix_file  optional output path of sorted file, else "gene_sorted-" + matrix_file
"""

# Imports
import pandas as pd
import sys
import argparse


def sort_sparse_matrix(matrix_file, sorted_matrix_file=None):
	"""Sort the sparse matrix file by gene, barcode
		Arguments:
		matrix_file- sparse matrix file to sort
		sorted_matrix_file- optional output path of sorted file
		Outputs-
		output_name- gene, barcode sorted sparse matrix file, name is either sorted_matrix_file if provided, or "gene_sorted-" + matrix_file
	"""
	if sorted_matrix_file:
		# if the sorted path name is provided, use it as the output name
		output_name = sorted_matrix_file
	else:
		# otherwise if the sorted path name is not provided, add "gene_sorted-" to the original path name
		output_name = "gene_sorted-" + matrix_file
	# read sparse matrix
	print("Reading Sparse Matrix")
	headers = []
	with open(matrix_file) as matrix:
		line = next(matrix)
		i = 1
		while line.startswith("%"):
			headers = headers + [line]
			line = next(matrix)
			i += 1
		headers = headers + [line]
		df = pd.read_table(matrix, sep=" ", header=i, names=['genes', 'barcodes', 'expr'])
	# sort sparse matrix
	print("Sorting Sparse Matrix")
	df = df.sort_values(by=['genes', 'barcodes'])
	# save sparse matrix
	print("Saving Sparse Matrix to:", output_name)
	with open(output_name, "w+") as output:
		print(''.join(headers))
		output.write(''.join(headers))
	df.to_csv(output_name, sep=' ', index=False, header=0, mode="a")


def __main__(argv):
	"""Command Line parser for sort_sparse_matrix
	Inputs-
	command line arguments
	"""
	# create the argument parser
	parser = argparse.ArgumentParser()
	# add argumnets
	parser.add_argument('matrix_file', help='Sparse Sparse Matrix file')
	parser.add_argument('--sorted_matrix_file', '-o', help='Gene sorted sparse matrix file path', default=None)
	# call sort_sparse_matrix with parsed args
	args = parser.parse_args()
	sort_sparse_matrix(matrix_file=args.matrix_file, sorted_matrix_file=args.sorted_matrix_file)
# python default
if __name__ == '__main__':
	__main__(sys.argv)