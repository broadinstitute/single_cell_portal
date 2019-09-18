"""Unit tests for scp_to_infercnv.py

To run, set up scripts per README, then:

cd scripts
python3 tests/test_scp_to_infercnv.py

"""

import unittest
from glob import glob
import json

import sys
sys.path.append('.')

from scp_to_infercnv import *

class ScpToInfercnvTestCase(unittest.TestCase):

    def test_conversion_with_references(self):
        """Converter should handle default case with reference clusters
        """
        output_dir = 'test_output/'

        args = [
            '--reference-cluster-path', 'tests/data/toy_cluster.txt',
            '--reference-group-name', 'toy-cell-types', 
            '--metadata-path', 'tests/data/toy_metadata.txt',
            '--observation-group-name', 'samples',
            '--output-dir', output_dir
        ]
        
        args = create_parser().parse_args(args)
        
        ref_list = get_references(args.ref_cluster_path,
            args.ref_group_name, args.delimiter)
        infercnv_annots = get_infercnv_annots(args.metadata_path,
            args.obs_group_name, args.delimiter, ref_list[0])
        write_infercnv_inputs(infercnv_annots, ref_list[1], args.output_dir)

        # Validate reference cells labels
        with open(output_dir + 'infercnv_reference_cell_labels_from_scp.tsv') as f:
            ref_labels = f.read()
        expected_ref_labels = 'ref_1,ref_2,ref_3,ref_4,ref_5,ref_6'
        self.assertEqual(ref_labels, expected_ref_labels)

        # Validate inferCNV annotations for reference cells
        with open(output_dir + 'infercnv_annots_from_scp.tsv') as f:
            infercnv_annots = [row.strip().split() for row in f.readlines()]
        expected_infercnv_annots_ref = [
            ['A', 'ref_1'],
            ['B', 'ref_2'],
            ['C', 'ref_2']
        ]
        infercnv_annots_ref = infercnv_annots[:3]  # Reference cells include the first three
        self.assertEqual(infercnv_annots_ref, expected_infercnv_annots_ref)

        # Validate inferCNV annotations for observation cells
        infercnv_annots_obs = infercnv_annots[-3:]  # Observations cells include the last three
        expected_infercnv_annots_obs = [
            ['CT_2', 'sample_3'], 
            ['CU_2', 'sample_1'], 
            ['CV_2', 'sample_2']
        ]
        self.assertEqual(infercnv_annots_obs, expected_infercnv_annots_obs)

if __name__ == '__main__':
    unittest.main()