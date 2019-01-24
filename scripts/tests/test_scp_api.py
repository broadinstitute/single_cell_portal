import requests
import unittest
from unittest.mock import patch
import json

import sys
sys.path.append('.')

import SCPAPI

# This method will be used by the mock to replace requests.get
def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    if args[0] == 'https://portals.broadinstitute.org/single_cell/api/v1/studies':
        with open('tests/data/studies.json') as f:
            content = f.read()
        studies_json = json.loads(content, strict=False)
        return MockResponse(studies_json, 200)

    return MockResponse(None, 404)

class SCPAPITestCase(unittest.TestCase):

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_get_studies(self, mock_get):
        scp_api = SCPAPI.SCPAPIManager()
        studies = scp_api.get_studies()['studies']
        expected_studies = [
            " Single nucleus RNA-seq of cell diversity in the adult mouse hippocampus (sNuc-Seq)",
            "Study only for unit test"
        ]
        self.assertEqual(studies, expected_studies)

if __name__ == '__main__':
    unittest.main()