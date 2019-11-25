import unittest
import sys
import pytest

sys.path.append('.')

from manage_study import validate_metadata_file

class ManageStudyTestCase(unittest.TestCase):

    def test_validate_metadata_file_invalid_ontology(self):
        """Unconventional metadata file should fail validation

        This basic test ensures that the external dependency
        `scp-ingest-pipeline` in our public CLI works as expected.
        """
        invalid_metadata_path = 'tests/data/invalid_array_v1.1.3.tsv'
        with self.assertRaises(SystemExit) as cm:
            validate_metadata_file(invalid_metadata_path)
        self.assertEqual(cm.exception.code, 1)
        

    def test_validate_metadata_file_valid_ontology(self):
        """Conventional metadata file should pass validation
        """
        valid_metadata_path = 'tests/data/valid_array_v1.1.3.tsv'
        validate_metadata_file(valid_metadata_path)

if __name__ == "__main__":
    unittest.main()
