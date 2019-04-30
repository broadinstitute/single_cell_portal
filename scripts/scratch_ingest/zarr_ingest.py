import zarr
import numpy as np
import sys
import json
import os



zarr_file = sys.argv[1]
zarr_file_name = os.path.splitext(zarr_file)[0]
##opens zar file and returns zarr.hierarchy.Group
za = zarr.open(zarr_file, mode='r')

#map expression values to genes
expression_matrix= dict(zip(za['expression_matrix']['gene_id'][:].tolist(), za['expression_matrix']['expression'][:].tolist()))

##save to zar file in js
with open('zarr.json', 'w') as outfile:
    json.dump(expression_matrix, outfile)

##Save to firestore
##Abstract this out
# def add_data_to_firestore(data):
#     batch = db.batch()
#     for key,val in data.items():
#         doc_ref = db.collection("loom_genes").document(key)
#         batch.set(doc_ref,
#         {"expression_valuess":val,
#         "file_name": zarr_file_name,
#         "cell_id": za['expression_matrix']['cell_id'][:10]
#         })
#     batch.commit()
#
# def chunk(data, SIZE=500):
#     it = iter(data)
#     for i in range(0, len(data), SIZE):
#        # if return_data_structure = dictionary:
#         yield {k:data[k] for k in islice(it, SIZE)}

# for genes in chunk(expression_matrix):
#     add_data_to_firestore(genes)
