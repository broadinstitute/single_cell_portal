import requests
import unittest
from unittest.mock import patch
import json

import sys
sys.path.append('.')

import scp_api

# TODO: Incorporate into `test_upload_cluster`
# def mock_upload_via_gsutil(*args, **kwargs):
#     gsutil_stat = {
#         'Content-Type': 'test/foo',
#         'Content-Length': '555',
#         'Generation': 'foo'
#     }
#     filename = 'fake_path.txt'
#     return [gsutil_stat, filename]

# This method will be used by the mock to replace requests.get
def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data
    
    url = args[0]
    if url == 'https://portals.broadinstitute.org/single_cell/api/v1/studies':
        with open('tests/data/studies.json') as f:
            content = f.read()
        studies_json = json.loads(content, strict=False)
        return MockResponse(studies_json, 200)

    return MockResponse(None, 404)

# This method will be used by the mock to replace requests.post
def mocked_requests_post(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    url = args[0]
    print('mock post url')
    print(url)

    study_files_url_re = '/v1/studies/.*/study_files'
    if re.match(study_files_url_re, url):
        with open('tests/data/study_files_post.json') as f:
            content = f.read()
        study_files_json = json.loads(content, strict=False)
        return MockResponse(studies_json, 200)

    parse_url_re = '/v1/studies/.*/study_files/.*/parse'
    if re.match(parse_url_re, url):
        return MockResponse(None, 204)

    return MockResponse(None, 404)

class SCPAPITestCase(unittest.TestCase):

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_get_studies(self, mocked_requests_get):
        manager = scp_api.SCPAPIManager()
        manager.api_base = 'https://portals.broadinstitute.org/single_cell/api/v1/'
        manager.verify_https = True
        studies = manager.get_studies()['studies']
        expected_studies = [
            " Single nucleus RNA-seq of cell diversity in the adult mouse hippocampus (sNuc-Seq)",
            "Study only for unit test"
        ]
        self.assertEqual(studies, expected_studies)

    # TODO: Finish this test per SCP-1897
    # @patch('scp_api.upload_via_gsutil', side_effect=mock_upload_via_gsutil)
    # @patch('requests.post', side_effect=mocked_requests_post)
    # @patch('requests.get', side_effect=mocked_requests_get)
    # def test_upload_cluster(self, mocked_requests_get, mocked_requests_post, mock_upload_via_gsutil):
    #     manager = scp_api.SCPAPIManager()
    #     manager.api_base = 'https://portals.broadinstitute.org/single_cell/api/v1/'
    #     manager.verify_https = True
    #     return_object = manager.upload_cluster(file='../tests/data/toy_cluster',
    #                                 study_name='CLI test',
    #                                 cluster_name='Test',
    #                                 description='Test',
    #                                 x='X', y='Y', z='Z',
    #                                 dry_run=True)
    #     print(f'test POST return object: {return_object}')
    #     # self.assertEqual(studies, expected_studies)

if __name__ == '__main__':
    unittest.main()