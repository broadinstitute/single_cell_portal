"""Command-line interface for ingesting zarr files into firestore

DESCRIPTION
This CLI maps cell ids to expression values, and gene ids from
a zarr file and puts them into firestore.

PREREQUISITES
You must have google cloud firestore installed, authenticated
and configured.

EXAMPLES
# Takes zarr file and stores it into firestore
$ python zarr_ingest.py  200k_subsample_4k_PMBC.zarr
"""


import sys
import json
import os
import time
from itertools import islice

from google.cloud import firestore
import zarr
import numpy as np


db = firestore.Client()
np.set_printoptions(precision=8, threshold=sys.maxsize, edgeitems=1e9)
expression_matrix = dict()

parser = argparse.ArgumentParser(
    prog = 'zarr_ingest.py'
)

parser.add_argument(
    "zarr_file", default=None,
    help='Path to loom file'
)

args = parser.parse_args()

##opens zar file and returns zarr.hierarchy.Group and file name
def open_file(zarr_file):
    return zarr.open(zarr_file, mode='r'), os.path.splitext(zarr_file)[0]

#map expression values to genes
def map_cell_ids_to_expression_values():
    expression_matrix.update(dict(zip(za['expression_matrix']['cell_id'][0:1000].tolist(), za['expression_matrix']['expression'][0:1000,0:500].tolist())))

##Save to firestore
##Abstract this out
def add_data_to_firestore(data):
    batch = db.batch()
    for key,val in data.items():
        exp_val = dict(zip(za['expression_matrix']['gene_id'][0:500].tolist(),val))
        doc_ref = db.collection("zarr_cells").document(key)
        batch.set(doc_ref,
        {
        "file_name": zarr_file_name,
        "gene_expression_values":{
        "expression_values":exp_val
        }
        })
    batch.commit()
    time.sleep(2)

def chunk(data, SIZE=5):
    it = iter(data)
    for i in range(0, len(data), SIZE):
        yield {k:data[k] for k in islice(it, SIZE)}

za, zarr_file_name = open_file(args.zarr_file)
map_cell_ids_to_expression_values()
for genes in chunk(expression_matrix):
    add_data_to_firestore(genes)
