import numpy as np
import loompy
import sys
import os
import  pyrebase
from google.cloud import firestore
from itertools import islice
import time

db = firestore.Client()

np.set_printoptions(precision=8, threshold=sys.maxsize, edgeitems=1e9)
expression_dictionaries= dict()
loom_file = sys.argv[1]
loom_file_name = os.path.splitext(loom_file)[0]

ds = loompy.connect(loom_file)

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

map_genes_to_expression_values()
for genes in chunk(expression_dictionaries):
    add_data_to_firestore(genes)

ds.close()
