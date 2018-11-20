"""Parse cell cluster and cell annotation metadata for downstream use in Ideogram.js

This module is a helper for matrix_to_ideogram_annots.py.
"""

def get_cluster_labels(cell_annotation_path, cell_annotation_name):
    cluster_labels = set()

    with open(cell_annotation_path) as f:
        lines = f.readlines()

    # This doesn't seem robust.
    cell_annotation_index = 3

    header = lines[0].strip().split('\t')[cell_annotation_index]

    for line in lines[2:]:
        columns = line.strip().split('\t')
        cluster_label = columns[cell_annotation_index]
        cluster_labels.add(cluster_label)

    return cluster_labels, cell_annotation_index

def get_clusters_meta(names, paths, metadata_path):
    """Organize cluster args provided via CLI into a more convenient dict"""
    clusters_meta = {
        'cluster_names': names,
        'cluster_paths': paths,
        'metadata_path': metadata_path
    }

    for i, name in enumerate(names):
        path = paths[i]
        cluster_labels, cell_annot_index = get_cluster_labels(path, name)
        cluster = {
            'cell_annot_labels': cluster_labels,
            'cell_annot_index': cell_annot_index
        }
        clusters_meta[name] = cluster

    # TODO: Handle cluster labels from metadata file

    return clusters_meta