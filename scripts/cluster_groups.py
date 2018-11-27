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

    got_all_cells = False
    all_cells = []

    for cluster_index, type in enumerate(types):
        if type != 'group':
            continue

        name = names[cluster_index]

        clusters[name] = {}

        for line in lines[3:]:
            columns = line.strip().split('\t')
            cluster_label = columns[cluster_index].strip()
            cell = columns[0]
            if got_all_cells is False:
                all_cells.append(cell)
            if cluster_label in clusters[name]:
                clusters[name][cluster_label].append(cell)
            else:
                clusters[name][cluster_label] = [cell]

        got_all_cells = True

    return [clusters, all_cells]

def get_cluster_groups(group_names, paths, metadata_path):
    """Organize cluster args provided via CLI into a more convenient dict"""
    cluster_groups = {}

    for i, path in enumerate(paths):
        group_name = group_names[i]
        clusters, cells = get_clusters_from_file(path)
        cluster_groups[group_name] = {
            'cells': cells,
            'cluster_file': clusters
        }
        
    metadata_clusters, cells = get_clusters_from_file(metadata_path)

    for group_name in cluster_groups:
        cluster_groups[group_name]['metadata_file'] = metadata_clusters

    for group_name in cluster_groups:
        print('group_name')
        print(group_name)
        print('clusters from cluster file')
        print(cluster_groups[group_name]['cluster_file'].keys())
        print('clusters from metadata file')
        print(cluster_groups[group_name]['metadata_file'].keys())
        metadata_clusters = cluster_groups[group_name]['metadata_file']
        for cluster_name in metadata_clusters:
            for label in metadata_clusters[cluster_name]:
                print('cells in ' + cluster_name + '/' + label + ':')
                print(len(metadata_clusters[cluster_name][label]))

    return cluster_groups