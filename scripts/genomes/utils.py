"""Common functions for genome assembly and annotation data processing.
"""

import gzip
import json
import multiprocessing
import os
import shutil
import subprocess
import time
import urllib.request as request

from google.cloud import storage
from google.oauth2 import service_account

def get_species_list(organisms_path):
    """Get priority species to support in Single Cell Portal
    """
    with open(organisms_path) as f:
        raw_species_list = [line.strip().split('\t') for line in f.readlines()[1:]]
        species_list = [line for line in raw_species_list if line[0][0] != '#']
    return species_list

def fetch_gzipped_content(url, output_path):
    """Fetch remote gzipped content, or read it from disk if cached
    """
    if os.path.exists(output_path):
        print('Reading cached gzipped ' + output_path)
        # Use locally cached content if available
        with open(output_path, 'rb') as f:
            content = ''
            #content = gzip.GzipFile(fileobj=f).readlines()
    else:
        print('Fetching gzipped ' + url)
        # If local report absent, fetch remote content and cache it
        request_obj = request.Request(
            url,
            headers={"Accept-Encoding": "gzip"}
        )
        with request.urlopen(request_obj) as response:
            remote_content = gzip.GzipFile(fileobj=response)
            remote_content = response.read()
            with open(output_path, 'wb') as f:
                f.write(remote_content)

            # Decompress foo.gtf.gz to foo.gtf
            output_path_uncompressed = output_path.replace('.gz', '')
            with open(output_path_uncompressed, 'wb') as f_out:
                with gzip.open(output_path, 'rb') as f_in:
                    shutil.copyfileobj(f_in, f_out)

            content = remote_content
    print('Returning content for gzipped ' + url)
    return content

def fetch_content(url_and_output_paths):
    """Fetch remote content, or read it from disk if cached
    """
    content_dict = {}
    for url_and_output_path in url_and_output_paths:
        url, output_path = url_and_output_path
        if url[-3:] == '.gz':
            content = fetch_gzipped_content(url, output_path)
        else:
            if os.path.exists(output_path):
                # Use locally cached content if available
                print('Reading cached ' + output_path)
                with open(output_path) as f:
                    content = f.readlines()
            else:
                # If local report absent, fetch remote content and cache it
                print('Fetching ' + output_path)
                with request.urlopen(url) as response:
                    remote_content = response.read().decode('utf-8')
                    with open(output_path, 'w') as f:
                        f.write(remote_content)
                    content = remote_content.split('\n')
        content_dict[output_path] = content
    return content_dict

def chunkify(lst, n):
    """Chunk a big list into smaller lists, each of length n
    """
    return [lst[i::n] for i in range(n)]

def get_pool_args(urls, output_dir, num_cores):
    """Gets chunked URL and output path arguments for multicore fetch
    """

    url_and_output_paths = []
    output_paths = [output_dir + url.split('/')[-1] for url in urls]
    for i, url in enumerate(urls):
        url_and_output_paths.append([url, output_paths[i]])

    if num_cores < len(url_and_output_paths):
        num_chunks = num_cores
    else:
        num_chunks = len(url_and_output_paths)
    chunked_url_and_output_paths = chunkify(url_and_output_paths, num_chunks)

    return chunked_url_and_output_paths

def batch_fetch(urls, output_dir):
    """Fetch content from multiple URLs (or read cache), in parallel
    """
    batch_contents = []

    # TODO:
    # Each file takes up ~2 GiB.  So multicore use can crash due to limited
    # memory. Use psutil to set determine free memory, then do something like:
    #
    #   free_memory = psutil.memory(...)... # Whatever the syntax is.
    #   num_cores_mem = free_memory / 2 GiB
    #   num_cores_raw = multiprocessing.cpu_count() - 1
    #   if num_cores_mem < num_cores_raw
    #       num_cores = num_cores_mem
    #   else:
    #       num_cores = num_cores_raw

    num_cores = 3 # Low multiple is a decent way to keep some memory free
    chunked_url_and_output_paths = get_pool_args(urls, output_dir, num_cores)

    with multiprocessing.Pool(processes=num_cores) as pool:
        for content_dict in pool.map(fetch_content, chunked_url_and_output_paths):
            for output_path in content_dict:
                content = content_dict[output_path]
                batch_contents.append([output_path, content])

    return batch_contents

def get_gcs_storage_client(vault_path):
    """Get Google Cloud Storage storage client for service account
    """

    # Get GCS SA credentials from Vault
    vault_command = ('vault read -format=json ' + vault_path).split(' ')
    p = subprocess.Popen(vault_command, stdout=subprocess.PIPE)
    vault_response = p.communicate()[0]
    gcs_info = json.loads(vault_response)['data']

    project_id = 'single-cell-portal'
    credentials = service_account.Credentials.from_service_account_info(gcs_info)
    storage_client = storage.Client(project_id, credentials=credentials)

    return storage_client

def upload_gcs_blob(bucket_name, source_file_name, destination_blob_name, storage_client):
    """Uploads a file to the bucket."""
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print('File {} uploaded to {}.'.format(
        source_file_name,
        destination_blob_name))

def copy_gcs_data_from_prod_to_dev(bucket, prod_dir, dev_dir):
    """Copy all GCS prod contents to GCS dev, to ensure they're equivalent
    """
    prod_blobs = bucket.list_blobs(prefix=prod_dir)
    print('prod blobs')
    for prod_blob in prod_blobs:
        prod_blob_name = prod_blob.name
        print(prod_blob_name)
        #bucket.copy_blob(source_blob, destination_bucket, new_blob_name)