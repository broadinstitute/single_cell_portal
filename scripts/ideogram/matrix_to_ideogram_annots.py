"""Produce Ideogram.js annotations from cluster data and gene expression matrix

This pipeline transforms data on cell clusters and gene expression matrices
into Ideogram.js annotations that depict genome-wide gene expression in
chromosome context.

For example, it can take an expression matrix processed by inferCNV
(https://github.com/broadinstitute/inferCNV) and cluster data in the form of
an SCP metadata file and SCP cluster files, and output Ideogram annotation
files for each cluster, with Ideogram tracks for each cluster label.  Such
ideograms can intuitively depict structural variants, e.g. losses of entire
chromosome arms as observed in some cancers.

Example:

python3 scripts/ideogram/matrix_to_ideogram_annots.py \
--matrix-path expression_pre_vis_transform.txt \
--gen-pos-file gencode_v19_gene_pos.txt \
--cluster-names "tSNE" "tSNE_non_malignant_cells" \
--cluster-paths tsne.txt tsne.non.mal.txt \
--metadata-path metadata.txt \
--output-dir ./

"""

from argparse import ArgumentParser, RawDescriptionHelpFormatter
import json
import os
import shutil
from statistics import mean
import tarfile

from cluster_groups import *

def make_tarfile(output_filename, source_dir):
    with tarfile.open(output_filename, 'w:gz') as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))

class MatrixToIdeogramAnnots:

    def __init__(self, matrix_path, matrix_delimiter, gen_pos_file,
                 cluster_groups, output_dir, heatmap_thresholds_path):
        """Class and parameter docs in module summary and argument parser"""

        self.matrix_path = matrix_path
        self.matrix_delimiter = matrix_delimiter
        self.cluster_groups = cluster_groups
        if output_dir[-1] != '/':
            output_dir += '/'
        self.output_dir = output_dir
        self.genomic_position_file_path = gen_pos_file
        ht_path = heatmap_thresholds_path
        self.heatmap_thresholds = parse_heatmap_thresholds(ht_path)

        self.genes = self.get_genes()

        self.write_ideogram_annots()

    def write_ideogram_annots(self):
        """Write Ideogram.js annotations JSON data to specified output file"""

        output_dir = self.output_dir

        ideogram_annots_list = self.get_ideogram_annots()
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.mkdir(output_dir)

        exp_means_zip_dir = output_dir + 'ideogram_exp_means/'
        if os.path.exists(exp_means_zip_dir):
            shutil.rmtree(exp_means_zip_dir)
        os.mkdir(exp_means_zip_dir)

        for group_name, scope, cluster_name, ideogram_annots in ideogram_annots_list:
            ideogram_annots_json = json.dumps(ideogram_annots)
            scope_map = {'cluster_file': 'cluster', 'metadata_file': 'study'}
            scope = scope_map[scope]
            identifier = group_name + '--' + cluster_name + '--group--' + scope
            file_name = 'ideogram_exp_means__' + identifier + '.json'
            output_path = exp_means_zip_dir + file_name
            with open(output_path, 'w') as f:
                f.write(ideogram_annots_json)

            print('Wrote Ideogram.js annotations to ' + output_path)

        output_gzip_file = output_dir + 'ideogram_exp_means.tar.gz'
        make_tarfile(output_gzip_file, exp_means_zip_dir)
        print('Packaged output into ' + output_gzip_file)

    def get_ideogram_annots(self):
        """Get Ideogram.js annotations from expression matrix and cluster data

        Format and other details of Ideogram.js annotations:
        https://github.com/eweitz/ideogram/wiki/Annotations
        """

        ideogram_annots_list = []

        genes = self.genes

        matrix = self.get_expression_matrix_dict()

        missing_genes = {}

        for group_name in self.cluster_groups:
            cluster_group = self.cluster_groups[group_name]
            for scope in ['cluster_file', 'metadata_file']:
                for cluster_name in cluster_group[scope]:

                    expression_means = self.compute_gene_expression_means(matrix, cluster_group, scope, cluster_name)

                    keys = ['name', 'start', 'length']
                    keys += list(cluster_group[scope][cluster_name].keys())  # cluster labels

                    annots_by_chr = {}

                    for i, expression_mean in enumerate(expression_means[1:]):
                        gene_id = expression_mean[0]
                        if gene_id in genes:
                            gene = genes[gene_id]
                        else:
                            missing_genes[gene_id] = 1
                            continue

                        chr = gene['chr']
                        start = int(gene['start'])
                        stop = int(gene['stop'])
                        length = stop - start

                        if chr not in annots_by_chr:
                            annots_by_chr[chr] = []

                        annot = [gene_id, start, length]

                        if i % 1000 == 0 and i != 0:
                            print('Constructed ' + str(i) + ' of ' + str(len(expression_means) - 1) + ' annots')

                        annot += expression_mean[1:]

                        annots_by_chr[chr].append(annot)

                    annots_list = []

                    for chr in annots_by_chr:
                        annots = annots_by_chr[chr]
                        annots_list.append({'chr': chr, 'annots': annots})

                    ideogram_annots = {
                        'keys': keys,
                        'metadata': {'heatmapThresholds': self.heatmap_thresholds},
                        'annots': annots_list
                    }
                    ideogram_annots_list.append([group_name, scope, cluster_name, ideogram_annots])

        if len(missing_genes) > 0:
            print('Genes in matrix but not in gene position file:')
            print(len(missing_genes))
            print('First such missing gene:')
            print(list(missing_genes.keys())[0])

        return ideogram_annots_list

    def get_genes(self):
        """Convert inferCNV genomic position file into useful 'genes' dict

        TODO: Use a standard GTF file instead of inferCNV-specific file
        """

        genes = {}

        with open(self.genomic_position_file_path) as f:
            lines = f.readlines()

        for line in lines:
            columns = line.strip().split()
            id, chr, start, stop = columns
            genes[id] = {
                'id': id,
                'chr': chr,
                'start': start,
                'stop': stop
            }

        return genes

    def get_expression_matrix_dict(self):
        """Parse expression matrix, return dict of cell expressions by gene"""
        print(self.get_expression_matrix_dict.__doc__)

        em_dict = {}

        with open(self.matrix_path) as f:
            lines = f.readlines()

        cells_dict = {}

        cells_list = lines[0].strip().split(self.matrix_delimiter)

        for i, cell in enumerate(cells_list):
            cell = cell.strip('"')
            if "PREVIZ" in cell:
                cell = cell.split('PREVIZ.')[1]  # "PREVIZ.AAACATACAAGGGC.1" -> AAACATACAAGGGC-1
            cell = cell.replace('.', '-')
            cells_dict[cell] = i

        em_dict['cells'] = cells_dict
        genes = {}

        for line in lines[1:]:
            columns = line.strip().split(self.matrix_delimiter)
            gene = columns[0].strip('"')
            expression_by_cell = list(map(float, columns[1:]))
            if gene == 'name':
                continue
            genes[gene] = expression_by_cell

        em_dict['genes'] = genes

        return em_dict

    def compute_gene_expression_means(self, matrix, cluster_group, scope, cluster_name):
        """Compute mean expression for each gene across each cluster"""

        scores_lists = []

        cells = matrix['cells']

        # print('cells')
        # print(cells)

        cluster_labels = list(cluster_group[scope][cluster_name].keys())

        keys = ['name'] + cluster_labels
        scores_lists.append(keys)

        gene_expression_lists = matrix['genes']

        # For each gene, get its mean expression in each cluster (a.k.a. ordination)
        for i, gene in enumerate(gene_expression_lists):

            gene_exp_list = gene_expression_lists[gene]

            scores_list = [gene]

            cluster = cluster_group[scope][cluster_name]
            for cluster_label in cluster:
                # cell_annot = cluster[name]
                cell_annot_expressions = []
                for cell in cluster[cluster_label]:
                    if cell not in cells: continue
                    index_of_cell_in_matrix = cells[cell] - 1
                    gene_exp_in_cell = gene_exp_list[index_of_cell_in_matrix]
                    cell_annot_expressions.append(gene_exp_in_cell)
                if len(cell_annot_expressions) == 0: continue
                mean_cluster_expression = round(mean(cell_annot_expressions), 3)
                scores_list.append(mean_cluster_expression)

            if i % 1000 == 0 and i != 0:
                print(
                    'Processed ' + str(i) + ' of ' + str(len(gene_expression_lists)) + ' ' + 
                    'for ' + scope + ', cluster ' + cluster_name
                )

            scores_lists.append(scores_list)

        scores_lists.reverse()
        return scores_lists

def parse_heatmap_thresholds(path):
    """Parses file containing rows of numbers, i.e. heatmap thresholds
    """
    if path is None: return None
    with open(path) as f:
        thresholds = [float(x.strip()) for x in f.readlines()]
        return thresholds

def create_parser():
    """Set up parsing for command-line arguments
    """
    parser = ArgumentParser(description=__doc__,  # Use text from file summary up top
                        formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--matrix-path',
                    help='Path to expression matrix file')
    parser.add_argument('--matrix-delimiter',
                    help='Delimiter in expression matrix',
                    default='\t')
    parser.add_argument('--gen-pos-file',
                    help='Path to gen_pos.txt genomic positions file from inferCNV')
    parser.add_argument('--cluster-names',
                    help='Names of cluster groups',
                    nargs='+')
    parser.add_argument('--ref-cluster-names',
                    help='Names of reference (normal) cluster groups',
                    nargs='+', default=[])
    parser.add_argument('--ordered-labels',
                    help='Sorted labels for clusters',
                    nargs='+', default=[])
    parser.add_argument('--heatmap-thresholds-path',
                    help='Path to heatmap thresholds file', required=False)
    # parser.add_argument('--ref-heatmap-thresholds',
    #                 help='Numeric thresholds for heatmap of reference (normal) cluster groups',
    #                 nargs='+', required=False)
    parser.add_argument('--cluster-paths',
                    help='Path or URL to cluster group files',
                    nargs='+')
    parser.add_argument('--metadata-path',
                    help='Path or URL to metadata file')
    parser.add_argument('--output-dir',
                    help='Path to write output')

    return parser

def convert_matrix_and_write(args):
    matrix_path = args.matrix_path
    matrix_delimiter = args.matrix_delimiter
    gen_pos_file = args.gen_pos_file
    cluster_names = args.cluster_names
    ref_cluster_names = args.ref_cluster_names
    ordered_labels = args.ordered_labels
    heatmap_thresholds_path = args.heatmap_thresholds_path
    # ref_heatmap_thresholds = args.ref_heatmap_thresholds
    cluster_paths = args.cluster_paths
    metadata_path = args.metadata_path
    output_dir = args.output_dir

    clusters_groups = get_cluster_groups(cluster_names, cluster_paths,
        metadata_path, ref_cluster_names=ref_cluster_names, ordered_labels=ordered_labels)

    MatrixToIdeogramAnnots(matrix_path, matrix_delimiter, gen_pos_file,
        clusters_groups, output_dir, heatmap_thresholds_path)

if __name__ == '__main__':
    args = create_parser().parse_args()
    convert_matrix_and_write(args)