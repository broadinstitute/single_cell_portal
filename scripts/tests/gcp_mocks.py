"""Mocks for Google Cloud Platform (GCP) services

These mocks enable tests to run in a manner that is fast and isolated.
GCP aspires to provide "emulators" for these services; see
https://github.com/googleapis/google-cloud-python/issues/4840.
Until those are available, custom mocks like these are the best available
alternative to enable integration tests to run quickly.
"""

import os
from shutil import copyfile


def mock_storage_client():
    class MockStorageBucket:
        def __init__(self, name):
            self.name = name
            return

        def blob(self, blob_name):
            return mock_storage_blob(bucket=self.name, name=blob_name)

    class MockStorageClient:
        def __init__(self):
            return

        def get_bucket(bucket_name):
            return MockStorageBucket(bucket_name)

    return MockStorageClient


def mock_storage_blob(*args, **kwargs):
    """Mocks Google Cloud Storage library

    TODO: Watch progress on official Storage emulator for integration tests:
        - https://github.com/googleapis/google-cloud-python/issues/8728
        - https://github.com/googleapis/google-cloud-python/issues/4840

    When such an emulator is released, use it and remove this custom mock.
    """

    class MockStorageBlob:
        def __init__(self, bucket=None, name=None):
            self.bucket = bucket
            self.name = 'tests/data/' + name
            print(f'Bucket is {self.bucket} and name is {self.name}')

        def exists(self, storage_client):
            return os.path.exists(self.name)

        def download_to_filename(self, filename):
            """Mock; doesn't actually download.  Makes local copy instead."""
            copyfile(self.name, filename)

    return MockStorageBlob(*args, **kwargs)
