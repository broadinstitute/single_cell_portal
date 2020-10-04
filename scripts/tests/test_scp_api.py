import requests
import unittest
from unittest.mock import patch
import json
import re

import sys

sys.path.append(".")

import scp_api

# TODO: Incorporate into `test_upload_cluster`
def mock_upload_via_gsutil_study_bucket_true(*args, **kwargs):
    gsutil_stat = {
        "Content-Type": "test/foo",
        "Content-Length": "555",
        "Generation": "foo",
    }
    filename = "fake_path.txt"
    file_from_study_bucket = True
    return [gsutil_stat, filename, file_from_study_bucket]


def mock_upload_via_gsutil_study_bucket_false(*args, **kwargs):
    gsutil_stat = {
        "Content-Type": "test/foo",
        "Content-Length": "555",
        "Generation": "foo",
    }
    filename = "fake_path.txt"
    file_from_study_bucket = False
    return [gsutil_stat, filename, file_from_study_bucket]


# This method will be used by the mock to replace requests.get
def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code, reason=None):
            self.json_data = json_data
            self.status_code = status_code
            self.reason = reason

        def json(self):
            return self.json_data

    url = args[0]
    if url == "https://singlecell.broadinstitute.org/single_cell/api/v1/studies":
        with open("tests/data/studies.json") as f:
            content = f.read()
        studies_json = json.loads(content, strict=False)
        return MockResponse(studies_json, 200, reason="OK")

    if (
        url
        == "https://singlecell.broadinstitute.org/single_cell/api/v1/studies/11114a35421aa904f7922101"
    ):
        ingest_mismatch_json = {
            "error": 'scp-ingest-pipeline: 0.9.12 incompatible with host, please update via "pip install scp-ingest-pipeline --upgrade"'
        }
        return MockResponse(ingest_mismatch_json, 400)

    return MockResponse(None, 404)


# This method will be used by the mock to replace requests.post
def mocked_requests_post(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code, reason=None):
            self.json_data = json_data
            self.status_code = status_code
            self.reason = reason

        def json(self):
            return self.json_data

    url = args[0]
    # study_id for " Single nucleus RNA-seq of cell diversity in the adult mouse hippocampus (sNuc-Seq)"
    # is 577d4a35421aa904f7922101
    upload_existing_file_url = "/v1/studies/577d4a35421aa904f7922101/study_files$"
    if re.search(upload_existing_file_url, url):
        unprocessable_entity_json = {
            "errors": {"file_type": ["You may only add one metadata file per study"]}
        }
        return MockResponse(unprocessable_entity_json, 422)

    study_files_url_re = "/v1/studies/.*/study_files$"
    if re.search(study_files_url_re, url):
        with open("tests/data/study_files_post.json") as f:
            content = f.read()
        study_files_json = json.loads(content, strict=False)
        return MockResponse(study_files_json, 200, reason="OK")

    parse_url_re = "/v1/studies/.*/study_files/.*/parse$"
    if re.search(parse_url_re, url):
        return MockResponse(None, 204)

    return MockResponse(None, 404)


class SCPAPITestCase(unittest.TestCase):
    @patch("requests.get", side_effect=mocked_requests_get)
    def test_get_studies(self, mocked_requests_get):
        manager = scp_api.SCPAPIManager()
        manager.api_base = "https://singlecell.broadinstitute.org/single_cell/api/v1/"
        manager.verify_https = True
        manager.head = {"Accept": "application/json"}
        studies = manager.get_studies()["studies"]
        expected_studies = [
            " Single nucleus RNA-seq of cell diversity in the adult mouse hippocampus (sNuc-Seq)",
            "Study only for unit test",
        ]
        self.assertEqual(studies, expected_studies)

    @patch("requests.get", side_effect=mocked_requests_get)
    def test_ingest_version_mismatch(self, mocked_ingest_version_mismatch):
        manager = scp_api.SCPAPIManager()
        manager.api_base = "https://singlecell.broadinstitute.org/single_cell/api/v1/"
        manager.verify_https = True
        manager.head = {
            "Accept": "application/json",
            "User-Agent": "single-cell-portal/0.1.3rc1 (manage-study) scp-ingest-pipeline/0.9.12 (ingest_pipeline.py)",
        }

        # All SCP servers use single-cell-portal major release v1 or later, sending
        # User-Agent string with an outdated package version should fail
        with self.assertRaises(SystemExit) as cm:
            manager.get_study_attribute(
                study_name="Study only for unit test", attribute="accession"
            )
        # 400 "incompatibile with server" response should trigger custom exit code 79
        self.assertEqual(
            cm.exception.code, 79
        ), "expect exit if ingest major version mismatch detected"

    @patch(
        "scp_api.SCPAPIManager.exists_in_bucket",
        return_value=True,
    )
    def test_upload_via_gsutil_remote_preexists(self, mock_exists_in_bucket):

        with self.assertRaises(SystemExit) as cm:
            scp_api.SCPAPIManager.upload_via_gsutil(
                bucket_id="foo", file_path="gs://baz/bar"
            )
        # If exists_in_bucket is True, exit-file-already-exists-in-study-bucket
        self.assertEqual(
            cm.exception.code, 80
        ), "expect exit if filename of remote file also exists in study bucket"

    @patch(
        "scp_api.SCPAPIManager.exists_in_bucket",
        return_value=False,
    )
    def test_upload_via_gsutil_missing_in_study_bucket(self, mock_exists_in_bucket):

        with self.assertRaises(SystemExit) as cm:
            scp_api.SCPAPIManager.upload_via_gsutil(
                bucket_id="foo", file_path="gs://foo/bar"
            )
        # If filepath uses study bucket but file is missing, expect exit
        self.assertEqual(
            cm.exception.code, 81
        ), "expect exit if file does not exists in study bucket"

    @patch(
        "scp_api.SCPAPIManager.upload_via_gsutil",
        side_effect=mock_upload_via_gsutil_study_bucket_true,
    )
    @patch("requests.post", side_effect=mocked_requests_post)
    @patch("requests.get", side_effect=mocked_requests_get)
    def test_upload_unprocessable_entity_study_bucket_true(
        self,
        mock_upload_via_gsutil_study_bucket_true,
        mocked_requests_post,
        mocked_requests_get,
    ):
        manager = scp_api.SCPAPIManager()
        manager.api_base = "https://singlecell.broadinstitute.org/single_cell/api/v1/"
        manager.verify_https = True
        manager.login(dry_run=True)

        # 422 response (unprocessable entity) from server
        # causes script to exit during file upload request
        with self.assertRaises(SystemExit) as cm:
            manager.upload_study_file(
                file="fc-36f39ea7-1111-4a49-ad10-6a5a4614300e/foo.txt",
                file_type="Metadata",
                study_name=" Single nucleus RNA-seq of cell diversity in the adult mouse hippocampus (sNuc-Seq)",
            )
        # when file_from_study_bucket = True, no cleanup in bucket occurs
        self.assertEqual(cm.exception.code, 84), "expect exit-no-file-cleanup-needed"

    @patch(
        "scp_api.SCPAPIManager.upload_via_gsutil",
        side_effect=mock_upload_via_gsutil_study_bucket_false,
    )
    @patch("requests.post", side_effect=mocked_requests_post)
    @patch("requests.get", side_effect=mocked_requests_get)
    @patch(
        "scp_api.SCPAPIManager.delete_via_gsutil",
        return_value=True,
    )
    def test_upload_unprocessable_entity_study_bucket_false(
        self,
        mocked_requests_get,
        mocked_requests_post,
        mock_upload_via_gsutil_study_bucket_false,
        mock_delete_via_gsutil,
    ):
        manager = scp_api.SCPAPIManager()
        manager.api_base = "https://singlecell.broadinstitute.org/single_cell/api/v1/"
        manager.verify_https = True
        manager.login(dry_run=True)

        with self.assertRaises(SystemExit) as cm:
            manager.upload_study_file(
                file="gs://fc-36f39ea7-439e-4a49-ad10-6a5a4614300e/metadata.txt",
                file_type="Metadata",
                study_name=" Single nucleus RNA-seq of cell diversity in the adult mouse hippocampus (sNuc-Seq)",
            )
        # when file_from_study_bucket = True, uploaded file is deleted from study bucket
        self.assertEqual(cm.exception.code, 83), "expect exit-uploaded-file-deleted"

    @patch(
        "scp_api.SCPAPIManager.upload_via_gsutil",
        side_effect=mock_upload_via_gsutil_study_bucket_true,
    )
    @patch("requests.post", side_effect=mocked_requests_post)
    @patch("requests.get", side_effect=mocked_requests_get)
    def test_upload_cluster(
        self,
        mocked_requests_get,
        mocked_requests_post,
        mock_upload_via_gsutil_study_bucket_true,
    ):
        # manager = scp_api.SCPAPIManager(verbose=True)
        manager = scp_api.SCPAPIManager()
        manager.api_base = "https://singlecell.broadinstitute.org/single_cell/api/v1/"
        manager.verify_https = True
        manager.login(dry_run=True)
        return_object = manager.upload_cluster(
            file="../tests/data/toy_cluster",
            study_name="Study only for unit test",
            cluster_name="Test",
            description="Test",
            x="X",
            y="Y",
            z="Z",
        )
        # HTTP 204 indicates successful parse launch, per
        # https://singlecell.broadinstitute.org/single_cell/api/swagger_docs/v1#!/StudyFiles/parse_study_study_file_path
        self.assertEqual(return_object["code"], 204)


if __name__ == "__main__":
    unittest.main()
