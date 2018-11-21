"""Parse cell cluster and cell annotation metadata for downstream use in Ideogram.js

This module is a helper for matrix_to_ideogram_annots.py.
"""

def get_labels_from_cluster_file(cell_annotation_path, cell_annotation_name):
    cluster_labels = set()

    with open(cell_annotation_path) as f:
        lines = f.readlines()

    # This seems fragile.
    cell_annotation_index = 3

    header = lines[0].strip().split('\t')[cell_annotation_index]

    for line in lines[2:]:
        columns = line.strip().split('\t')
        cluster_label = columns[cell_annotation_index]
        cluster_labels.add(cluster_label)

    return cluster_labels, cell_annotation_index

def get_clusters_from_metadata_file(metadata_path):
    metadata_clusters = {}

    with open(metadata_path) as f:
        lines = f.readlines()

    headers = [line.strip().split('\t') for line in lines[:2]]
    names = headers[0]
    types = headers[1]

    for cluster_index, type in enumerate(types):
        if type != 'group':
            continue

        cluster_labels = set()

        name = 'METADATA__' + names[cluster_index]

        for line in lines[3:]:
            columns = line.strip().split('\t')
            cluster_label = columns[cluster_index].strip()
            cluster_labels.add(cluster_label)

        metadata_clusters[name] = [cluster_labels, cluster_index]

    return metadata_clusters

def get_clusters_meta(names, paths, metadata_path):
    """Organize cluster args provided via CLI into a more convenient dict"""
    clusters_meta = {
        'cluster_names': names,
        'cluster_paths': paths,
        'metadata_path': metadata_path
    }

    for i, name in enumerate(names):
        path = paths[i]
        labels, index = get_labels_from_cluster_file(path, name)
        cluster = {
            'cell_annot_labels': labels,
            'cell_annot_index': index
        }
        clusters_meta[name] = cluster

    metadata_clusters = get_clusters_from_metadata_file(metadata_path)
    for name in metadata_clusters:
        labels, index = metadata_clusters[name]
        cluster = {
            'cell_annot_labels': labels,
            'cell_annot_index': index
        }
        clusters_meta[name] = cluster
    clusters_meta['cluster_names'] += list(metadata_clusters.keys())

    print('clusters_meta')
    print(clusters_meta)

    return clusters_meta