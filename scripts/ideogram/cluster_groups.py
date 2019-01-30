"""Parse cell cluster and cell annotation metadata for downstream use in Ideogram.js

This module is a helper for matrix_to_ideogram_annots.py.
"""

import pprint
pp = pprint.PrettyPrinter(indent=4)

def get_clusters_from_file(path, ref_cluster_names=[]):
    """Get cluster names, labels, and cells from cluster file or metadata file
    """
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
            if cluster_label in ref_cluster_names:
                continue
            cell = columns[0]
            if got_all_cells is False:
                all_cells.append(cell)
            if cluster_label in clusters[name]:
                clusters[name][cluster_label].append(cell)
            else:
                clusters[name][cluster_label] = [cell]

        got_all_cells = True

    return [clusters, all_cells]

def order_labels(cluster_groups, group_name, source, ordered_labels):
    clusters = cluster_groups[group_name][source]
    for cluster_name in clusters:
        cluster = clusters[cluster_name]
        ordered_cluster = {}
        if ordered_labels is None:
            ordered_cluster = cluster
        else:
            for label in ordered_labels:
                ordered_cluster[label] = cluster[label]
        cluster_groups[group_name][source][cluster_name] = ordered_cluster
        for label in cluster:
            num_cells = str(len(cluster[label]))
            print('  Cells in ' + cluster_name + '/' + label + ': ' + num_cells)

    return cluster_groups

def get_cluster_groups(group_names, paths, metadata_path, ref_cluster_names=None):
    """Get cluster groups data structure from raw passed CLI arguments"""
    cluster_groups = {}

    print('group_names')
    print(group_names)

    print('paths')
    print(paths)

    print('metadata_path')
    print(metadata_path)

    print('ref_cluster_names')
    print(ref_cluster_names)

    for i, path in enumerate(paths):
        group_name = group_names[i]
        clusters, cells = get_clusters_from_file(path, ref_cluster_names=ref_cluster_names)
        cluster_groups[group_name] = {
            'cells': cells,
            'cluster_file': clusters
        }

    metadata_clusters, cells = get_clusters_from_file(metadata_path, ref_cluster_names=ref_cluster_names)

    for group_name in cluster_groups:
        cluster_groups[group_name]['metadata_file'] = metadata_clusters

    print('cluster_groups')
    print(cluster_groups)

    ordered_labels = None
    # ordered_labels = [
    #     'malignant_97',
    #     'malignant_93',
    #     'malignant_MGH53',
    #     'malignant_MGH36'
    # ]

    # Print number of cells in each cluster label, for each cluster
    # (annotation), scope, and group
    for group_name in cluster_groups:
        print('Cluster group: ' + group_name)
        metadata_clusters = cluster_groups[group_name]['metadata_file']
        print('From metadata file:')
        source = 'metadata_file'
        cluster_groups = order_labels(cluster_groups, group_name, source, ordered_labels)
        print('From cluster file:')
        source = 'cluster_file'
        cluster_groups = order_labels(cluster_groups, group_name, source, ordered_labels)

    return cluster_groups