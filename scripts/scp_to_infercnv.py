"""Convert SCP metadata and cluster files to inferCNV annotation file

inferCNV runs require specifying the names of reference (i.e. normal, control)
cell groups, which are headers in an annotation file passed into inferCNV.  SCP
has files that contain annotations including cell groups, but not quite in the
format needed for inferCNV annotation files.  This script does the needed
transformation.
"""

import argparse
import os

def write_infercnv_inputs(infercnv_annots, ref_labels, output_dir):
    """Write inferCNV annotations and reference labels to files
    """
    if output_dir[-1] != '/':
        output_dir += '/'

    if os.path.exists(output_dir) == False:
        os.mkdir(output_dir)

    output_path = output_dir + 'infercnv_annots_from_scp.tsv'
    with open(output_path, 'w') as f:
        f.write(infercnv_annots)
    print('Wrote inferCNV annotations file to: ' + output_path)

    output_path = output_dir + 'infercnv_reference_cell_labels_from_scp.tsv'
    with open(output_path, 'w') as f:
        f.write(ref_labels)
    print('Wrote inferCNV reference cell labels to: ' + output_path)

def get_references(cluster_path, ref_group_name, delimiter):
    """Parse SCP cluster file, return inferCNV reference cells and labels
    """
    # Reference (normal) cell annotations, i.e. cell name and group label
    ref_annots = {}

    with open(cluster_path) as f:
        cluster_rows = f.readlines()

    groups = cluster_rows[0].strip().split(delimiter)
    group_index = groups.index(ref_group_name)

    # Reference cell labels
    ref_labels = set()

    for row in cluster_rows[2:]:  # Skip header rows
        columns = row.strip().split(delimiter)
        cell = columns[0]
        label = columns[group_index]
        ref_labels.add(label)
        ref_annots[cell] = label

    ref_labels = ','.join(ref_labels)

    return [ref_annots, ref_labels]

def get_infercnv_annots(metadata_path, obs_group_name, delimiter, ref_annots):
    """Parse SCP metadata file, return inferCNV annotations list

    The SCP metadata file categorizes all cells in the expression matrix
    provided to inferCNV.  However, it does not specify which cells to use as
    reference (normal) nor how to label those reference cells in inferCNV.
    That information is in ref_annots.
    """

    infercnv_annots = []

    with open(metadata_path) as f:
        metadata_rows = f.readlines()

    groups = metadata_rows[0].strip().split(delimiter)
    group_index = groups.index(obs_group_name)

    # For all cells, get their label from the metadata file, unless
    # the cell is a reference cell, in which case use its label from
    # the previously-parsed SCP cluster file.
    for row in metadata_rows[2:]:  # Skip header rows
        columns = row.strip().split(delimiter)
        cell = columns[0]
        if cell in ref_annots:
            label = ref_annots[cell]
        else:
            label = columns[group_index]
        infercnv_annots.append(cell + '\t' + label)
    infercnv_annots = '\n'.join(infercnv_annots)

    return infercnv_annots

def create_parser():
    """Set up parsing for command-line arguments
    """
    parser = argparse.ArgumentParser(description=__doc__,  # Use text from file summary up top
                        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--reference-cluster-path',
                    dest='ref_cluster_path',
                    help='Path to SCP cluster file to use as reference ' +
                    '(i.e. normal, control) cells')
    parser.add_argument('--reference-group-name',
                    dest='ref_group_name',
                    help='Name of cell group in SCP cluster file to use as ' +
                    'label for inferCNV references')
    parser.add_argument('--metadata-path',
                    help='Path to SCP metadata file that contains all cells')
    parser.add_argument('--observation-group-name',
                    dest='obs_group_name',
                    help='Name of the cell group in SCP metadata file to ' +
                    'use as label for observations')
    parser.add_argument('--delimiter',
                    help='Delimiter in SCP cluster file',
                    default="\t")
    parser.add_argument('--output-dir',
                    help='Path to write output')
    return parser

if __name__ == '__main__':
    args = create_parser().parse_args()
    ref_list = get_references(args.ref_cluster_path,
        args.ref_group_name, args.delimiter)
    infercnv_annots = get_infercnv_annots(args.metadata_path,
        args.obs_group_name, args.delimiter, ref_list[0])
    write_infercnv_inputs(infercnv_annots, ref_list[1], args.output_dir)