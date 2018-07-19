import argparse
import csv
import os
import shutil

CLUSTER_DELIM = ","
METADATA_FILE_ID = "NAME"
METADATA_TYPE = "TYPE"
METADATA_GROUP = "group"
CLUSTER_GROUP = "numeric"
CLUSTER_HEADERS = ['X', 'Y', 'Z']

class Matrix:

    def __init__(self):
        self.row_ids = {}
        self.col_ids = {}
        self.data = {}

    def add_value(self, feature, column, value):
        if feature and column:
            if feature not in self.row_ids:
                self.row_ids[feature] = None
            if column not in self.col_ids:
                self.col_ids[column] = None
            self.data.setdefault(column, {})[feature] = value
            return(True)
        else:
            return(False)

    def write_to_file(self, file, file_type='metadata'):
        if os.path.exists(file):
            print("File already exists, will not write over files. File:"+str(file))
            return(False)
        cols = [i for i in self.col_ids.keys()]
        rows = [i for i in self.row_ids.keys()]

        output = []
        if file_type == 'metadata':
            output.append([METADATA_FILE_ID] + cols)
            output.append([METADATA_TYPE] + [METADATA_GROUP]*len(cols))
        elif file_type == 'cluster':
            if len(cols) > 3:
                print("Cannot create a cluster file with more than 3 dimensions.")
                return(False)
            output.append([METADATA_FILE_ID] + CLUSTER_HEADERS[:len(cols)])
            output.append([METADATA_TYPE] + [CLUSTER_GROUP] * len(cols))

        for row in rows:
            output.append([row] + [ self.data[col_id][row] for col_id in cols ])
        with open(file,'w') as file_open:
            file_writer = csv.writer(file_open, delimiter = "\t")
            file_writer.writerows(output)
            print("Wrote file "+str(file))
        return(True)


def add_metadata_file(file, num_col, matrix, key=""):
    if  not file or not os.path.exists(file):
        print("Could not find file:"+str(file))
        return(False)
    with open(file,'r') as open_file:
        contents = csv.reader(open_file, delimiter=CLUSTER_DELIM)
        headers = next(contents)
        if key:
            headers = [key+"_"+header for header in headers]
        if num_col > len(headers)+1:
            print("This file does not have "+str(num_col+1)+" columns.")
            num_col = len(headers) - 1
            print("Only storing "+str(num_col)+" columns.")
        for line in contents:
            for col_id in range(1,num_col+1):
                matrix.add_value(line[0],headers[col_id],line[col_id])
    return(True)

prsr_arguments = argparse.ArgumentParser(
    prog="cell_ranger_to_scp.py",
    description="Convert Cell Ranger output to SCP file formats",
    conflict_handler="resolve",
    formatter_class=argparse.HelpFormatter)

# New file names
prsr_arguments.add_argument("--tsne_coordinates_file",
                            dest="tsne_file_name",
                            help="tSNE-base coordinates file")

prsr_arguments.add_argument("--pca_coordinates_file",
                            dest="pca_file_name",
                            help="pca-base coordinates file")

prsr_arguments.add_argument("--metadata_file",
                            dest="metadata_file_name",
                            help="metadata portal file")

prsr_arguments.add_argument("--other_directory",
                            dest="other_dir_name",
                            help="The directory to put other files in.")

## Metadata
prsr_arguments.add_argument("--tsne",
                            dest="tsne",
                            help="outs/analysis/tsne/2_components/projection.csv file")

prsr_arguments.add_argument("--pca",
                            dest="pca",
                            help="outs/analysis/pca/10_components/projection.csv file")

prsr_arguments.add_argument("--graphclust",
                            dest="graphclust",
                            help="outs/analysis/clustering/graphclust/clusters.csv file")

prsr_arguments.add_argument("--kmeans_2",
                            dest="kmeans_2",
                            help="outs/analysis/clustering/kmeans_2_clusters/clusters.csv file")

prsr_arguments.add_argument("--kmeans_3",
                            dest="kmeans_3",
                            help="outs/analysis/clustering/kmeans_3_clusters/clusters.csv file")

prsr_arguments.add_argument("--kmeans_3",
                            dest="kmeans_3",
                            help="outs/analysis/clustering/kmeans_3_clusters/clusters.csv file")

prsr_arguments.add_argument("--kmeans_4",
                            dest="kmeans_4",
                            help="outs/analysis/clustering/kmeans_4_clusters/clusters.csv file")

prsr_arguments.add_argument("--kmeans_5",
                            dest="kmeans_5",
                            help="outs/analysis/clustering/kmeans_5_clusters/clusters.csv file")

prsr_arguments.add_argument("--kmeans_6",
                            dest="kmeans_6",
                            help="outs/analysis/clustering/kmeans_6_clusters/clusters.csv file")

prsr_arguments.add_argument("--kmeans_7",
                            dest="kmeans_7",
                            help="outs/analysis/clustering/kmeans_7_clusters/clusters.csv file")

prsr_arguments.add_argument("--kmeans_8",
                            dest="kmeans_8",
                            help="outs/analysis/clustering/kmeans_8_clusters/clusters.csv file")

prsr_arguments.add_argument("--kmeans_9",
                            dest="kmeans_9",
                            help="outs/analysis/clustering/kmeans_9_clusters/clusters.csv file")

prsr_arguments.add_argument("--kmeans_10",
                            dest="kmeans_10",
                            help="outs/analysis/clustering/kmeans_10_clusters/clusters.csv file")

prsr_arguments.add_argument("--other_files",
                            default = [],
                            dest="other",
                            nargs="*",
                            help="Files that are not asked for specifically in this argument parser but are output and should be organized by this script.")

prs_args = prsr_arguments.parse_args()

## Move files that the portal does not interact with to an known output space
for file in prs_args.other:
    if file:
        if not prs_args.other_dir_name:
            print("Other directory should be given if other files are specified.")
            exit(89)
        if not os.path.exists(prs_args.other_dir_name):
            os.makedirs(prs_args.other_dir_name)
        try:
            shutil.move(file, prs_args.other_dir_name)

            print("Moved "+str(file))
        except EnvironmentError as err:
            print("Could not move file="+str(file))
            print(err)
            exit(96)

## Make metadata matrix
metadata = Matrix()
metadata_files = [[prs_args.graphclust,"graph"], [prs_args.kmeans_2,"kmeans2"],
                  [prs_args.kmeans_3,"kmeans3"], [prs_args.kmeans_4,"kmeans4"],
                  [prs_args.kmeans_5,"kmeans5"], [prs_args.kmeans_6,"kmeans6"],
                  [prs_args.kmeans_7,"kmeans7"], [prs_args.kmeans_8,"kmeans8"],
                  [prs_args.kmeans_9,"kmeans9"], [prs_args.kmeans_10,"kmeans10"]]
metadata_files = [ f for f in metadata_files if f[0] is not None ]
if len(metadata_files) > 0:
    if prs_args.metadata_file_name is None:
        print("Please provide a metadata file to write.")
        exit(92)
    for metadata_file, file_key in metadata_files:
        success = add_metadata_file(metadata_file, 1, metadata, file_key)
        if not success:
            print("Failed to add "+str(metadata_file))
            exit(99)
    metadata.write_to_file(prs_args.metadata_file_name)
metdata = None

## Make cluster files
if not prs_args.pca is None:
    if prs_args.pca_file_name is None:
        print("Please provide a file to write the pca projections")
        exit(90)
    cluster = Matrix()
    success = add_metadata_file(prs_args.pca, 3, cluster)
    if not success:
        print("Failed to add " + str(prs_args.pca))
        exit(98)
    cluster.write_to_file(prs_args.pca_file_name, 'cluster')

if not prs_args.tsne is None:
    if prs_args.tsne_file_name is None:
        print("Please provide a file to write the tSNE projections.")
        exit(91)
    cluster = Matrix()
    success = add_metadata_file(prs_args.tsne, 2, cluster)
    if not success:
        print("Failed to add " + str(prs_args.tsne))
        exit(97)
    cluster.write_to_file(prs_args.tsne_file_name, 'cluster')