"""Common functions for genome assembly and annotation data processing.
"""

import gzip
import os
import urllib.request as request

def get_species_list(organisms_path):
    """Get priority species to support in Single Cell Portal
    """
    with open(organisms_path) as f:
        species_list = [line.strip().split('\t') for line in f.readlines()[1:]]
    return species_list

def fetch_gzipped_content(url, output_path):
    """Fetch remote gzipped content, or read it from disk if cached
    """
    if os.path.exists(output_path):
        print('Reading cached ' + output_path)
        # Use locally cached content if available
        with open(output_path, 'rb') as f:
            content = gzip.GzipFile(fileobj=f).readlines()
    else:
        print('Fetching ' + output_path)
        # If local report absent, fetch remote content and cache it
        request_obj = request.Request(
            url,
            headers={"Accept-Encoding": "gzip"}
        )
        with request.urlopen(request_obj) as response:
            # remote_content = gzip.GzipFile(fileobj=response)
            remote_content = response.read()
            print(remote_content)
            with open(output_path, 'wb') as f:
                f.write(remote_content)
            content = remote_content
    return content

def fetch_content(url, output_path):
    """Fetch remote content, or read it from disk if cached
    """
    if url[-3:] == '.gz':
        return fetch_gzipped_content(url, output_path)

    if os.path.exists(output_path):
        # Use locally cached content if available
        with open(output_path) as f:
            content = f.readlines()
    else:
        # If local report absent, fetch remote content and cache it
        with request.urlopen(url) as response:
            remote_content = response.read().decode('utf-8')
            with open(output_path, 'w') as f:
                f.write(remote_content)
            content = remote_content.split('\n')
    return content