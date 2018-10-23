"""Download genome annotations, transform for igv.js, upload to GCS for SCP
"""

import argparse
import json
import os
import shutil
import subprocess
import urllib.request as request

from google.cloud import storage
from google.oauth2 import service_account

from utils import *

parser = argparse.ArgumentParser(
    description=__doc__, # Use docstring at top of file for --help summary
    formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument('--use_cache',
                    help='Whether to use cache',
                    action='store_true')
parser.add_argument('--vault_path',
                    help='Path in Vault for GCS service account credentials')
parser.add_argument('--output_dir',
                    help='Directory to send output data to.  Default: output/',
                    default='output/')
args = parser.parse_args()
use_cache = args.use_cache
vault_path = args.vault_path
output_dir = args.output_dir

scp_species = get_species_list('organisms.tsv')

def get_ensembl_metadata():
    """Get organism, assembly, and annotation release metadata from Ensembl
    """
    ensembl_metadata = {}

    # API docs: https://rest.ensembl.org/documentation/info/species
    url = 'https://rest.ensembl.org/info/species?content-type=application/json'
    with request.urlopen(url) as response:
        data = response.read().decode('utf-8')
    ensembl_species = json.loads(data)['species']

    for species in ensembl_species:
        taxid = species['taxon_id']
        name = species['name']
        assembly = species['assembly']
        strain = species['strain']

        if (taxid == '10090' and strain != 'reference (CL57BL6)'):
            # Mouse has multiple annotated assemblies; only use reference assembly
            continue

        ensembl_metadata[taxid] = {
            'organism': name,
            'taxid': taxid,
            'assembly_name': assembly,
            'assembly_accession': species['accession'],
            'release': str(species['release'])
        }

    return ensembl_metadata

def get_ensembl_gtf_urls(ensembl_metadata):
    """Construct the URL of an Ensembl genome annotation GTF file.

    Example URL:
    http://ftp.ensembl.org/pub/release-94/gtf/homo_sapiens/Homo_sapiens.GRCh38.94.gtf.gz
    """

    gtf_urls = []
    for species in scp_species:
        taxid = species[2]
        organism_metadata = ensembl_metadata[taxid]
        release = organism_metadata['release']
        organism = organism_metadata['organism']
        organism_upper = organism[0].upper() + organism[1:]
        assembly = organism_metadata['assembly_name']

        origin = 'http://ftp.ensembl.org'
        dir = '/pub/release-' + release + '/gtf/' + organism + '/'
        filename = organism_upper + '.' + assembly + '.' + release + '.gtf.gz'

        gtf_url = origin + dir + filename
        gtf_urls.append(gtf_url)
        ensembl_metadata[taxid]['gtf_path'] = output_dir + filename

    return [gtf_urls, ensembl_metadata]

def transform_ensembl_gtf(gtf_path, ref_dir):
    """Produce sorted GTF and GTF index from Ensembl GTF; needed for igv.js
    """
    # Example:
    # $ sort -k1,1 -k4,4n gencode.vM17.annotation.gtf > gencode.vM17.annotation.possorted.gtf
    # $ bgzip gencode.vM17.annotation.possorted.gtf
    # $ tabix -p gff gencode.vM17.annotation.possorted.gtf.gz
    sorted_filename = gtf_path.replace('.gtf', '.possorted.gtf')
    sorted_filename = ref_dir + sorted_filename.replace(output_dir, '')
    outputs = [sorted_filename + '.gz', sorted_filename + '.gz.tbi']
    if os.path.exists(outputs[1]):
        print('Using cached GTF transforms')
        return outputs
    else:
        print('Producing GTF transforms for ' + gtf_path)

    # sort by chromosome name, then genomic start position; needed for index
    sort_command = ('sort -k1,1 -k4,4n ' + gtf_path).split(' ')
    sorted_file = open(sorted_filename, 'w')
    subprocess.call(sort_command, stdout=sorted_file)

    # bgzip enables requesting small indexed chunks of a gzip'd file
    bgzip_command = ('bgzip ' + sorted_filename).split(' ')
    subprocess.call(bgzip_command)

    # tabix creates an index for the GTF file, used for getting small chunks
    tabix_command = ('tabix -p gff ' + sorted_filename + '.gz').split(' ')
    subprocess.call(tabix_command)

    return outputs

def make_local_reference_dirs(ensembl_metadata):
    """Create a folder hierarchy on this machine to mirror that planned for GCS
    """
    print('Making local reference directories')

    for species in scp_species:
        taxid = species[2]
        organism_metadata = ensembl_metadata[taxid]
        organism = organism_metadata['organism']
        asm_name = organism_metadata['assembly_name']
        asm_acc = organism_metadata['assembly_accession']
        release = 'ensembl_' + organism_metadata['release']
        folder = output_dir + 'reference_data_dev/'
        folder += organism + '/' + asm_name + '_' + asm_acc + '/' + release + '/'

        os.makedirs(folder, exist_ok=True)

        ensembl_metadata[taxid]['reference_dir'] = folder

    return ensembl_metadata

def transform_ensembl_gtfs(ensembl_metadata):
    """Download raw Ensembl GTFs, write position-sorted GTF and index
    """
    transformed_gtfs = []

    gtf_urls, ensembl_metadata = get_ensembl_gtf_urls(ensembl_metadata)
    gtfs = batch_fetch(gtf_urls, output_dir)
    ensembl_metadata = make_local_reference_dirs(ensembl_metadata)

    print('Got GTFs!  Number: ' + str(len(gtfs)))
    for species in scp_species:
        taxid = species[2]
        organism_metadata = ensembl_metadata[taxid]
        gtf_path = organism_metadata['gtf_path'].replace('.gz', '')
        ref_dir = organism_metadata['reference_dir']
        transformed_gtfs = transform_ensembl_gtf(gtf_path, ref_dir)

        ensembl_metadata[taxid]['transformed_gtfs'] = transformed_gtfs

    return ensembl_metadata

def get_gcs_storage_client():
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

def upload_ensembl_gtf_products(ensembl_metadata):
    print('Uploading Ensembl GTF products')

    storage_client = get_gcs_storage_client()

    # FireCloud workspace:
    # https://portal.firecloud.org/#workspaces/single-cell-portal/scp-reference-data
    scp_reference_data = 'fc-bcc55e6c-bec3-4b2e-9fb2-5e1526ddfcd2'
    top_bucket_folder = 'reference_data_dev/'

    bucket = storage_client.get_bucket(scp_reference_data)
    
    existing_blob_names = [blob.name for blob in bucket.list_blobs()]

    for species in scp_species:
        taxid = species[2]
        organism_metadata = ensembl_metadata[taxid]
        transformed_gtfs = organism_metadata['transformed_gtfs']
        for transformed_gtf in transformed_gtfs:
            source_blob_name = transformed_gtf
            target_blob_name = source_blob_name.replace('output/', '')
            if target_blob_name in existing_blob_names:
                print('Already in bucket, not uploading: ' + target_blob_name)
                continue
            blob = bucket.blob(target_blob_name)
            blob.upload_from_filename(source_blob_name)
            print('Uploaded to GCS: ' + target_blob_name)

if use_cache is False:
    if os.path.exists(output_dir) is False:
        print('Cache unavailable, starting fresh run')
    else:
        print('Deleting output cache from previous run')
        shutil.rmtree(output_dir)

if os.path.exists(output_dir) is False:
    os.mkdir(output_dir)

ensembl_metadata = get_ensembl_metadata()
ensembl_metadata = transform_ensembl_gtfs(ensembl_metadata)
upload_ensembl_gtf_products(ensembl_metadata)