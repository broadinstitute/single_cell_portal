"""Unit tests for matrix_to_ideogram_annots.py

To run, set up scripts per README, then:

cd scripts
python3 ideogram/tests/test_matrix_to_ideogram_annots.py

"""

import unittest
from glob import glob
import json

import sys
sys.path.append('ideogram')

from matrix_to_ideogram_annots import create_parser, convert_matrix_and_write

class MatrixToIdeogramAnnotsTestCase(unittest.TestCase):

    def test_conversion_with_references(self):
        """Converter should handle default case with reference clusters
        """
        output_dir = 'output_infercnv_example/'
        args = [
            '--matrix-path', 'ideogram/tests/data/oligodendroglioma_expression_truncated.counts.matrix.txt',
            '--gen-pos-file', 'ideogram/tests/data/gencode_v19_gene_pos_truncated_sorted.txt',
            '--cluster-names', 'Observations',
            '--ref-cluster-names', 'Microglia/Macrophage', 'Oligodendrocytes (non-malignant)',
            '--cluster-paths', 'ideogram/tests/data/oligodendroglioma_annotations_downsampled.cluster.txt',
            '--metadata-path', 'ideogram/tests/data/oligodendroglioma_annotations_downsampled.cluster.txt',
            '--output-dir', output_dir
        ]

        args = create_parser().parse_args(args)
        convert_matrix_and_write(args)

        end_output_dir = output_dir + 'ideogram_exp_means/'

        # Verify output file names
        files = sorted(glob(end_output_dir + '*'))
        expected_files = sorted([
            end_output_dir + 'ideogram_exp_means__Observations--Sample--group--study.json',
            end_output_dir + 'ideogram_exp_means__Observations--Sample--group--cluster.json'
        ])
        self.maxDiff = None
        print('files')
        print(files)
        print('expected_files')
        print(expected_files)
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

        # Test a particular Ideogram annotation
        annot = annots['annots'][0]['annots'][0]
        # gene name, genomic start, genomic length, expression value averages
        expected_annot = ['ACOX3', 8368009, 74441, 3.308, 2.154, 1.967, 2.687]
        self.assertEqual(annot, expected_annot)

    def test_conversion_without_references(self):
        """Converter should handle default case without reference clusters
        I.e., without values for --ref-cluster-names
        """
        output_dir = 'output_infercnv_example/'
        args = [
            '--matrix-path', 'ideogram/tests/data/oligodendroglioma_expression_truncated.counts.matrix.txt',
            '--gen-pos-file', 'ideogram/tests/data/gencode_v19_gene_pos_truncated_sorted.txt',
            '--cluster-names', 'Observations',
            '--cluster-paths', 'ideogram/tests/data/oligodendroglioma_annotations_downsampled.cluster.txt',
            '--metadata-path', 'ideogram/tests/data/oligodendroglioma_annotations_downsampled.cluster.txt',
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

        # Test a particular Ideogram annotation
        annot = annots['annots'][0]['annots'][0]
        # gene name, genomic start, genomic length, expression value averages
        expected_annot = ['ACOX3', 8368009, 74441, 0.726, 0.448, 3.308, 2.154, 1.967, 2.687]
        self.assertEqual(annot, expected_annot)

if __name__ == '__main__':
    unittest.main()