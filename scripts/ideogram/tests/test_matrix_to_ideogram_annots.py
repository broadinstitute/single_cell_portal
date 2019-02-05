"""Unit tests for matrix_to_ideogram_annots.py

To run, set up scripts per README, then:

cd scripts/ideogram/tests
python3 test_matrix_to_ideogram_annots.py

"""

import unittest
from glob import glob
import json

import sys
sys.path.append('..')

from matrix_to_ideogram_annots import create_parser, convert_matrix_and_write

class MatrixToIdeogramAnnotsTestCase(unittest.TestCase):

    def test_conversion_with_references(self):
        """Converter should handle default case with reference clusters
        """
        output_dir = 'output_infercnv_example/'
        args = [
            '--matrix-path', 'data/oligodendroglioma_expression_truncated.counts.matrix.txt',
            '--gen-pos-file', 'data/gencode_v19_gene_pos_truncated_sorted.txt',
            '--cluster-names', 'Observations',
            '--ref-cluster-names', 'Microglia/Macrophage', 'Oligodendrocytes (non-malignant)',
            '--cluster-paths', 'data/oligodendroglioma_annotations_downsampled.cluster.txt',
            '--metadata-path', 'data/oligodendroglioma_annotations_downsampled.cluster.txt',
            '--output-dir', output_dir
        ]

        args = create_parser().parse_args(args)
        convert_matrix_and_write(args)

        end_output_dir = output_dir + 'ideogram_exp_means/'

        # Verify output file names
        files = glob(end_output_dir + '*')
        expected_files = [
            end_output_dir + 'ideogram_exp_means__Observations--Sample--group--study.json',
            end_output_dir + 'ideogram_exp_means__Observations--Sample--group--cluster.json'
        ]
        self.assertEqual(files, expected_files)

        cluster_annots_file = end_output_dir + 'ideogram_exp_means__Observations--Sample--group--cluster.json'
        with open(cluster_annots_file) as f:
            annots = json.loads(f.read())

        # Verify keys in Ideogram annotation data
        keys = annots['keys']
        expected_keys = [
            'name', 'start', 'length',
            'malignant_MGH36', 'malignant_MGH53', 'malignant_97', 'malignant_93'
        ]
        self.assertEqual(keys, expected_keys)

    def test_conversion_without_references(self):
        """Converter should handle default case without reference clusters
        I.e., without values for --ref-cluster-names
        """
        output_dir = 'output_infercnv_example/'
        args = [
            '--matrix-path', 'data/oligodendroglioma_expression_truncated.counts.matrix.txt',
            '--gen-pos-file', 'data/gencode_v19_gene_pos_truncated_sorted.txt',
            '--cluster-names', 'Observations',
            '--cluster-paths', 'data/oligodendroglioma_annotations_downsampled.cluster.txt',
            '--metadata-path', 'data/oligodendroglioma_annotations_downsampled.cluster.txt',
            '--output-dir', output_dir
        ]

        args = create_parser().parse_args(args)
        convert_matrix_and_write(args)

        end_output_dir = output_dir + 'ideogram_exp_means/'

        cluster_annots_file = end_output_dir + 'ideogram_exp_means__Observations--Sample--group--cluster.json'
        with open(cluster_annots_file) as f:
            annots = json.loads(f.read())

        # Verify keys in Ideogram annotation data
        # Note additional elements for microglia and oligodendrocyte clusters
        keys = annots['keys']
        expected_keys = [
            'name', 'start', 'length',
            'Microglia/Macrophage', 'Oligodendrocytes (non-malignant)',
            'malignant_MGH36', 'malignant_MGH53', 'malignant_97', 'malignant_93'
        ]
        self.assertEqual(keys, expected_keys)

if __name__ == '__main__':
    unittest.main()