"""Parse cell cluster and cell annotation metadata for downstream use in Ideogram.js

This module is a helper for matrix_to_ideogram_annots.py.
"""

import pprint
pp = pprint.PrettyPrinter(indent=4)

def get_clusters_from_file(path):
    clusters = {}

    with open(path) as f:
        lines = f.readlines()

    headers = [line.strip().split('\t') for line in lines[:2]]
    names = headers[0]
    types = headers[1]

    for cluster_index, type in enumerate(types):
        if type != 'group':
            continue

        cluster_labels = set()

        name = names[cluster_index]

        for line in lines[3:]:
            columns = line.strip().split('\t')
            cluster_label = columns[cluster_index].strip()
            cluster_labels.add(cluster_label)

        clusters[name] = [cluster_labels, cluster_index]

    return clusters

def get_cluster_groups(group_names, paths, metadata_path):
    """Organize cluster args provided via CLI into a more convenient dict"""
    cluster_groups = {}

    group_names.append('METADATA')
    paths.append(metadata_path)

    for i, path in enumerate(paths):
        cluster_group_name = group_names[i]
        clusters = get_clusters_from_file(path)
        cluster_groups[cluster_group_name] = {
            'path': path,
            'clusters': {}
        }
        for name in clusters:
            labels, index = clusters[name]
            cluster = {
                'cell_annot_labels': labels,
                'cell_annot_index': index
            }
            cluster_groups[cluster_group_name]['clusters'][name] = cluster

    print('cluster_groups')
    pp.pprint(cluster_groups)

    return cluster_groups