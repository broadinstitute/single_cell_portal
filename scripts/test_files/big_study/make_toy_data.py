#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generate data to simulate large study, e.g. to test download features.

Example:
python make_toy_data.py
"""

from random import randrange, uniform
import argparse
import multiprocessing

args = argparse.ArgumentParser(
    prog="make_toy_data.py",
    description=(
        "Generate data to simulate large study, e.g. to test download " +
        "features."
    ),
    formatter_class=argparse.HelpFormatter
)
args.add_argument(
    "--num_files", default=3, type=int, dest="num_files",
    help="Number of toy data files output",
)
args.add_argument(
    "--num_cores", default=None, type=int, dest="num_cores",
    help="Number of CPUs to use",
)
parsed_args = args.parse_args()
num_files = parsed_args.num_files
num_cores = parsed_args.num_cores

def get_signature_content(prefix):
    """
    Generates "signature" data, incorporating a given prefix.

    This data is structurally similar to real data, but otherwise semantic
    and statistical noise.

    :param prefix: String of two uppercase letters, e.g. 'AB'
    :return: String of signature content, ~25 MB in size
    """

    letters = ['A', 'B', 'C', 'D']

    num_columns = 16584
    num_rows = 80

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
    file_name = prefix + '_toy_data_signature_50000.txt'
    with open(file_name, 'w') as f:
        f.write(content)
        print('Wrote ' + file_name)

prefixes = []

# Produce a number of text files, each ~25 MB
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