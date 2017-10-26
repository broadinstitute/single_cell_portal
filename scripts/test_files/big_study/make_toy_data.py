#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generate data to simulate large study, e.g. to test download features.

This data is structurally similar to real data, but otherwise semantic and
statistical noise.

Examples:

# Generate 3 files, 25 MB each
python make_toy_data.py

# Generate 6 files, 2 MB each
python make_toy_data.py --num_files=3 --size_per_file=2_MB

# Generate 1 file named AB_meso.txt, 2 GB in raw size, then compress it
python make_toy_data.py --num_files=1 filename_leaf="meso" --size_per_file=2_GB --gzip
"""

from random import randrange, uniform
import argparse
import multiprocessing
import gzip

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
    '--size_per_file', default="25_MB", dest='size_per_file',
    help=(
        '<filesize_value>_<filesize_unit_symbol>, ' +
        'e.g. 300_MB means 300 megabytes per file.  ' +
        'Note that we implicitly convert decimal units to binary units ' +
        '(e.g. MB -> MiB) because 1) most filesystems misreport binary as ' +
        'decimal and 2) understanding of binary prefixes is not widespread.'
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
parsed_args = args.parse_args()
num_files = parsed_args.num_files
filename_leaf = parsed_args.filename_leaf
size_per_file = parsed_args.size_per_file
gzip_files = parsed_args.gzip_files
num_cores = parsed_args.num_cores


def get_signature_content(prefix):
    """
    Generates "signature" data, incorporating a given prefix.

    :param prefix: String of two uppercase letters, e.g. "AB"
    :return: String of signature content, ~25 MB in size
    """

    letters = ['A', 'B', 'C', 'D']

    num_rows = 80
    bytes_per_column = 1.315*1024  # ~1.315 KB (KiB) per column, uncompressed
    num_columns = int(bytes_per_file/bytes_per_column)

    # Generate header
    header = "GENE\t"
    for i in range(1, num_columns):
        random_string = ''
        for j in range(1, 16):
            # Generate a 16-character string of random combinations of
            # letters A, B, C, and D
            ri1 = randrange(0, 4)  # Random integer between 0 and 3, inclusive
            random_string += letters[ri1]
        ri2 = str(randrange(1, 9))
        ri3 = str(randrange(1, 9))
        header += (
            'Foobar' + prefix +
            ri2 + '_BazMoo_' +
            ri3 + random_string + '-1\t'
        )

    # Generate values below header
    values = ''
    for i in range(1, num_rows):
        for j in range(1, num_columns):
            # Random number between 0 and -0.099999999999999
            random_small_float = uniform(0, 0.1) * -1
            values += str(random_small_float) + '\t'

    signature_data = header + '\n' + values
    return signature_data


def pool_processing(prefix):
    """ Function called by each CPU core in our pool of available CPUs
    """
    content = get_signature_content(prefix)
    file_name = prefix + '_toy_data_' + filename_leaf + '.txt'
    with open(file_name, 'w') as f:
        f.write(content)
        print('Wrote ' + file_name)


def parse_filesize_string(filesize_string):
    """ Returns number of bytes specified in a human-readable filesize string

    Note that we implicitly convert decimal units to binary units
    (e.g. MB -> MiB) because 1) most filesystems misreport binary as decimal,
    and 2) understanding of binary prefixes is not widespread.

    :param filesize_string: Filesize string, e.g. '300_MB'
    :return: num_bytes: Integer number of bytes, e.g. 307200000

    """
    fss = filesize_string.split('_')  # e.g. ['300', 'MB']
    filesize_value = float(fss[0])  # e.g. 300.0
    filesize_unit_symbol = fss[1][0]  # e.g. 'M'

    # Unit prefix: binary multiplier (in scientific notation)
    unit_multipliers = {'': 1, 'K': 1.024E3, 'M': 1.024E6, 'G': 1.024E9, 'T': 1.024E12}
    filesize_unit_multiplier = unit_multipliers[filesize_unit_symbol]

    num_bytes = int(filesize_value * filesize_unit_multiplier)

    return num_bytes


bytes_per_file = parse_filesize_string(size_per_file)
prefixes = []

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