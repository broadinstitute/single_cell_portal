"""
Swap column values, but not column headers, of a TSV file

Example:

# Swap values in first and last columns of a TSV that has two header lines
python3 swap_column_values.py --num_header_rows 2 --swap_columns 0,-1 --input_file scp_coordinates.tsv

"""

import argparse

args = argparse.ArgumentParser(
    prog='swap_column_values.py',
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter
)
args.add_argument(
    '--input_file', dest='input_file',
    help='Path to input TSV file'
)
args.add_argument(
    '--output_file', dest='output_file',
    help='Path to use for output TSV file.  Defaults to e.g. input_file.swapped.tsv'
)
args.add_argument(
    '--num_header_rows', default=1, type=int, dest='num_header_rows',
    help='Number of rows occupied by headers'
)
args.add_argument(
    '--swap_columns', dest='swap_columns', default='0,-1',
    help='Indexes of two columns to swap.  Defaults to first (1) and last (-1) columns.'
)

parsed_args = args.parse_args()
input_file = parsed_args.input_file
output_file = parsed_args.output_file
num_header_rows = parsed_args.num_header_rows
swap_columns = parsed_args.swap_columns

swap_indexes = [int(index) for index in swap_columns.split(',')]

with open(input_file) as f:
    lines = f.readlines()

headers = ''.join(lines[:num_header_rows])

value_lines = lines[num_header_rows:]

swapped_lines = []

for line in value_lines:
    split_line = line.strip().split('\t')
    column_1 = split_line[swap_indexes[0]]
    column_2 = split_line[swap_indexes[1]]
    swapped_line = split_line

    # Swap the two specified columns
    swapped_line[swap_indexes[0]] = column_2
    swapped_line[swap_indexes[1]] = column_1

    # Cast array to TSV string
    swapped_line = '\t'.join(swapped_line)

    swapped_lines.append(swapped_line)

swapped_lines = headers + '\n'.join(swapped_lines)

if output_file is None:
    split_input_path = input_file.split('.')
    output_path = split_input_path[:-1] + ['swapped', split_input_path[-1]]
    output_file = '.'.join(output_path)

with open(output_file, 'w') as f:
    f.write(swapped_lines)