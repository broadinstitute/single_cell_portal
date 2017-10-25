#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generate data to simulate large study, e.g. to test download features.

Example:
python make_toy_data.py
"""

from random import randrange, uniform


def get_signature_content(prefix):
    """
    Generates "signature" data, incorporating a given prefix.

    This data is structurally similar to real data, but otherwise semantic
    and statistical noise.

    :param prefix: String of two uppercase letters, e.g. 'AB'
    :return: String of signature content, ~25 MB in size
    """

    letters = ['A', 'B', 'C', 'D']

    num_items = 16584

    header = "GENE\t"

    for i in range(1, num_items):
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

    values = ''
    for i in range(1, 80):
        print('On item ' + str(i))
        for j in range(1, num_items):
            # Random number between 0 and -0.099999999999999
            random_small_float = uniform(0, 0.1) * -1
            values += str(random_small_float) + '\t'

    signature_data = header + '\n' + values
    return signature_data

# Produce three text files, each ~25 MB
prefixes = ['AB', 'CD', 'EF']
for prefix in prefixes:
    content = get_signature_content(prefix)
    with open(prefix + '_toy_data_signature_50000.txt', 'w') as f:
        f.write(content)
