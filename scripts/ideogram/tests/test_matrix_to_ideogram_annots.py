import unittest

import sys
sys.path.append('..')

from matrix_to_ideogram_annots import create_parser, convert_matrix_and_write

class MatrixToIdeogramAnnotsTestCase(unittest.TestCase):

    def test_conversion(self):
        output_dir = 'output_infercnv_example/'
        args = [
            '--matrix-path', '/Users/eweitz/inferCNV/example/oligodendroglioma_expression_downsampled.counts.matrix.txt',
            '--gen-pos-file', '/Users/eweitz/single_cell_portal/infercnv_test_data/infercnv/infercnv_gencode_v19_gene_pos.txt',
            '--cluster-names', 'Observations',
            '--cluster-paths', '/Users/eweitz/inferCNV/example/oligodendroglioma_annotations_downsampled.cluster.txt',
            '--metadata-path', '/Users/eweitz/inferCNV/example/oligodendroglioma_annotations_downsampled.cluster.txt',
            '--output-dir', output_dir
        ]

        args = create_parser().parse_args(args)
        convert_matrix_and_write(args)

        studies = []

        expected_studies = [
            " Single nucleus RNA-seq of cell diversity in the adult mouse hippocampus (sNuc-Seq)",
            "Study only for unit test"
        ]
        self.assertEqual(studies, expected_studies)

if __name__ == '__main__':
    unittest.main()