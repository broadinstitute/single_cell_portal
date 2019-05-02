"""Command-line interface for ingesting loom files into firestore

DESCRIPTION
This CLI maps genes to expression values, cell ids, gene accesions from
a loom file and puts them into firestore.

PREREQUISITES
You must have google could firestore installed, authenticated
 configured.

EXAMPLES
# Takes loom file and stores it into firestore
$ python loom_ingest.py  200k_subsample_4k_PMBC.loom
"""


import argparse
import time
import sys
import os
from itertools import islice

from google.cloud import firestore
import loompy
import numpy as np

expression_dictionaries = dict()
db = firestore.Client()

parser = argparse.ArgumentParser(
    prog ='loom_ingest.py'
)

parser.add_argument(
    "loom_file", default=None,
    help='Path to loom file'
)

args = parser.parse_args()
np.set_printoptions(precision=8, threshold=sys.maxsize, edgeitems=1e9)

##Opens loom file
def open_file(loom_file):
    return loompy.connect(loom_file), os.path.splitext(loom_file)[0]

##creating dictoionary
def map_genes_to_expression_values():
    for (ix, selection, view) in ds.scan(axis=0, batch_size=5000):
        #Firestore does not know how to store ndArrays
        exppressions_values = view[:,:].tolist()
        accessions = view.ra.Accession.tolist()
        cell_ids = view.ca.CellID.tolist()
        expression_dictionaries.update(zip(view.ra.Gene.tolist(),zip(accessions, cell_ids, exppressions_values)))

##Returns a subset (500) of dictionaries
def chunk(data, SIZE=500):
    it = iter(data)
    for i in range(0, len(data), SIZE):
        yield {k:data[k] for k in islice(it, SIZE)}

##Abstract this out
def add_data_to_firestore(data):
    batch = db.batch()
    ##Should only commit 500 writes to avoid contention
    #Need to measure write speeds and size of uploads
    for key,val in data.items():
        doc_ref = db.collection("loom_gene").document(key)
        batch.set(doc_ref, {
        'accession': val[0],
        'file_name' : loom_file,
        'cells':{
        'cell_id': val[1],
        'expression_values': val[2]
        }
        })
    batch.commit()
    time.sleep(2)

##Open loom file
ds, loom_file_name = open_file(args.loom_file)

#Map expression data to expression values and row attrobutes
map_genes_to_expression_vaues()
for genes in chunk(expression_dictionaries):
    add_data_to_firestore(genes)

ds.close()
