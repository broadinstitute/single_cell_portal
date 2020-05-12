import unittest
from unittest.mock import patch
import sys
import pytest

sys.path.append('.')

from manage_study import validate_metadata_file
from gcp_mocks import mock_storage_client, mock_storage_blob
from test_scp_api import mocked_requests_get

def connection
class ManageStudyTestCase(unittest.TestCase):


    @patch('requests.get', side_effect=mocked_requests_get)
    def test_validate_metadata_file_invalid_ontology(self, mock_storage_client, mock_storage_blob):
        """Unconventional metadata file should fail validation

        This basic test ensures that the external dependency
        `scp-ingest-pipeline` in our public CLI works as expected.
        """
        invalid_metadata_path = 'tests/data/invalid_array_v1.1.3.tsv'
        with self.assertRaises(SystemExit) as cm:
            validate_metadata_file(invalid_metadata_path)
        self.assertEqual(cm.exception.code, 1)

    @patch('google.cloud.storage.Blob', side_effect=mock_storage_blob)
    @patch('google.cloud.storage.Client', side_effect=mock_storage_client)
    def test_validate_metadata_file_valid_ontology(self, mock_storage_client, mock_storage_blob):
        """Conventional metadata file should pass validation
        """
        valid_metadata_path = 'tests/data/valid_array_v1.1.3.tsv'
        validate_metadata_file(valid_metadata_path)

if __name__ == "__main__":
    unittest.main()
