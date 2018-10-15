"""Common functions for genome assembly and annotation data processing.
"""

import gzip
import multiprocessing
import os
import time
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
        print('Reading cached gzipped ' + output_path)
        # Use locally cached content if available
        with open(output_path, 'rb') as f:
            content = gzip.GzipFile(fileobj=f).readlines()
    else:
        print('Fetching gzipped ' + output_path)
        # If local report absent, fetch remote content and cache it
        request_obj = request.Request(
            url,
            headers={"Accept-Encoding": "gzip"}
        )
        with request.urlopen(request_obj) as response:
            # remote_content = gzip.GzipFile(fileobj=response)
            remote_content = response.read()
            with open(output_path, 'wb') as f:
                f.write(remote_content)
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

    # num_cores = multiprocessing.cpu_count() - 1
    num_cores = 3
    chunked_url_and_output_paths = get_pool_args(urls, output_dir, num_cores)

    with multiprocessing.Pool(processes=num_cores) as pool:
        for content_dict in pool.map(fetch_content, chunked_url_and_output_paths):
            for output_path in content_dict:
                content = content_dict[output_path]
                batch_contents.append(content)

    return batch_contents