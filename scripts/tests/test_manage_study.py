import unittest
from unittest.mock import patch, Mock
import sys
import pytest
import json
import requests
from ingest.cell_metadata import CellMetadata
from ingest.validation.validate_metadata import (
    report_issues,
    serialize_issues,
    exit_if_errors,
    validate_input_metadata,
)
sys.path.append('.')

from manage_study import validate_metadata_file
from gcp_mocks import mock_storage_client, mock_storage_blob
from scp_api import SCPAPIManager
from cli_parser import create_parser

# This method will be used by the mock to replace requests.post
def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code, reason=None):
            self.json_data = json_data
            self.status_code = status_code
            self.reason = reason

        def json(self):
            return self.json_data

    url = args[0]
    convention_file_path= 'tests/data/alexandria_convention_schema_2.1.0.json'
    if url == 'metadata_schemas/alexandria_convention/latest/json':
        with open(convention_file_path) as f:
            return MockResponse(json.load(f), 200, reason='OK')
    return MockResponse(None, 404)

def mock_get_connection(*args, **kwargs):
    class MockResponse:
        def get_study_attribute(study_name,attribute, dry_run):
            return {'success': True, 'study_attribute': 'SCP599'}

        def do_get(command=None,dry_run=None):
            return {'response':mocked_requests_get(command)}

    return MockResponse

def mock_get_parsed_args():
    return Mock()

def mock_get_api_base():
    return ''

class ManageStudyTestCase(unittest.TestCase):
    def set_up_manage_study(self,*args):
        return create_parser().parse_args(args)

    @patch('manage_study.get_connection', side_effect=mock_get_connection)
    @patch('manage_study.succeeded', return_value=True)
    @patch('manage_study.get_parsed_args')
    @patch('manage_study.get_api_base', side_effect = mock_get_api_base)
    def test_validate_metadata_file_invalid_ontology(self,
        mock_get_connection,
        mock_succeeded,
        mock_get_parsed_args,
        mock_get_api_base):
        """Unconventional metadata file should fail validation

        This basic test ensures that the external dependency
        `scp-ingest-pipeline` in our public CLI works as expected.
        """
        mock_get_parsed_args.return_value = self.set_up_manage_study(
        'upload-metadata',
        '--study-name',
        'CLI test',
        '--file',
        'tests/data/invalid_array_v1.1.3.tsv',
        '--use-convention'
        )
        SCPAPIManager= Mock()
        SCPAPIManager.get_study_attribute.return_value= 'SCP555'

        invalid_metadata_path = 'tests/data/invalid_array_v1.1.3.tsv'
        with self.assertRaises(SystemExit) as cm:
            validate_metadata_file(invalid_metadata_path)
        self.assertEqual(cm.exception.code, 1)

    @patch('manage_study.get_connection', side_effect=mock_get_connection)
    @patch('manage_study.succeeded', return_value=True)
    @patch('manage_study.get_parsed_args')
    @patch('manage_study.get_api_base', side_effect = mock_get_api_base)
    def test_validate_metadata_file_valid_ontology(self,
        mock_get_connection,
        mock_succeeded,
        mock_get_parsed_args,
        mock_get_api_base):
        """Conventional metadata file should pass validation

        This basic test ensures that the external dependency
        `scp-ingest-pipeline` in our public CLI works as expected.
        """
        mock_get_parsed_args.return_value = self.set_up_manage_study(
        'upload-metadata',
        '--study-name',
        'CLI test',
        '--file',
        'tests/data/invalid_array_v1.1.3.tsv',
        '--use-convention'
        )
        SCPAPIManager= Mock()
        SCPAPIManager.get_study_attribute.return_value= 'SCP555'

        valid_metadata_path = 'tests/data/valid_array_v20.0.0.tsv'
        not self.assertRaises(SystemExit, validate_metadata_file(valid_metadata_path))
if __name__ == "__main__":
    unittest.main()
