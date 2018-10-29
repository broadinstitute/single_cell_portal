"""Download genome annotations, transform for visualizations, upload to GCS
"""

import argparse
import json
import os
import shutil
import subprocess
import urllib.request as request

from utils import *

parser = argparse.ArgumentParser(
    description=__doc__, # Use docstring at top of file for --help summary
    formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument('--use_cache',
                    help='Whether to use cache',
                    action='store_true')
parser.add_argument('--vault_path',
                    help='Path in Vault for GCS service account credentials')
parser.add_argument('--local_output_dir',
                    help='Local directory for output.  Default: output/',
                    default='output/')
parser.add_argument('--gcs_bucket',
                    help='Name of GCS bucket for upload.  ' +
                    'Default: reference_data_dev/',
                    default='fc-bcc55e6c-bec3-4b2e-9fb2-5e1526ddfcd2')
parser.add_argument('--remote_output_dir',
                    help='Remote directory for output in GCS bucket.  ' +
                    'Default: reference_data_dev/',
                    default='reference_data_dev/')
parser.add_argument('--copy_data_from_prod_dir',
                    help='Remote directory from which to copy data into ' +
                    'remote_output_dir.  Use to ensure test data ' +
                    'environment is equivalent to production data ' +
                    'environment.  Default: reference_data/',
                    default='reference_data/')
args = parser.parse_args()
use_cache = args.use_cache
vault_path = args.vault_path
gcs_bucket = args.gcs_bucket
output_dir = args.local_output_dir
remote_prod_dir = args.copy_data_from_prod_dir
remote_output_dir = args.remote_output_dir

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
        print('  Using cached GTF transforms')
        return outputs
    else:
        print('  Producing GTF transforms for ' + gtf_path)

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
        folder = output_dir + remote_output_dir
        folder += organism + '/' + asm_name + '_' + asm_acc + '/' + release + '/'

        os.makedirs(folder, exist_ok=True)

        ensembl_metadata[taxid]['reference_dir'] = folder

    return ensembl_metadata

def transform_ensembl_gtfs(ensembl_metadata):
    """Download raw Ensembl GTFs, write position-sorted GTF and index
    """
    transformed_gtfs = []

    gtf_urls, ensembl_metadata = get_ensembl_gtf_urls(ensembl_metadata)

    print('Fetching GTFs')
    gtfs = batch_fetch(gtf_urls, output_dir)
    print('Got GTFs!  Number: ' + str(len(gtfs)))

    ensembl_metadata = make_local_reference_dirs(ensembl_metadata)

    print('Transforming GTFs')
    for species in scp_species:
        taxid = species[2]
        organism_metadata = ensembl_metadata[taxid]
        gtf_path = organism_metadata['gtf_path'].replace('.gz', '')
        ref_dir = organism_metadata['reference_dir']
        transformed_gtfs = transform_ensembl_gtf(gtf_path, ref_dir)

        ensembl_metadata[taxid]['transformed_gtfs'] = transformed_gtfs

    return ensembl_metadata

def upload_gtf_product(transformed_gtf, bucket, existing_names):
    source_blob_name = transformed_gtf
    target_blob_name = source_blob_name.replace('output/', '')

    # Check if this file was already uploaded
    if target_blob_name in existing_names:
        print('  Already in bucket, not uploading: ' + target_blob_name)
        return target_blob_name

    # Upload the file
    blob = bucket.blob(target_blob_name)
    blob.upload_from_filename(source_blob_name)
    print('  Uploaded to GCS: ' + target_blob_name)

    return target_blob_name

def upload_ensembl_gtf_products(ensembl_metadata):
    print('Uploading Ensembl GTF products')

    storage_client = get_gcs_storage_client(vault_path)

    # FireCloud workspace for canonical SCP reference data:
    # https://portal.firecloud.org/#workspaces/single-cell-portal/scp-reference-data
    reference_data_bucket = gcs_bucket
    target_folder = remote_output_dir

    bucket = storage_client.get_bucket(reference_data_bucket)

    remote_dev_dir = remote_output_dir
    copy_gcs_data_from_prod_to_dev(bucket, remote_prod_dir, remote_dev_dir)
    
    existing_names = [blob.name for blob in bucket.list_blobs()]

    for species in scp_species:
        taxid = species[2]
        organism_metadata = ensembl_metadata[taxid]
        transformed_gtfs = organism_metadata['transformed_gtfs']

        for transformed_gtf in transformed_gtfs:
            target_name = upload_gtf_product(transformed_gtf, bucket,
                existing_names)

            # Update metadata with GTF product URLs
            origin = 'https://storage.cloud.google.com'
            gcs_url = origin + reference_data_bucket + target_name
            if gcs_url[-7:] == '.gtf.gz':
                product = 'annotation_url'
            elif gcs_url[-11:] == '.gtf.gz.tbi':
                product = 'annotation_index_url'
            ensembl_metadata[taxid][product] = gcs_url

    return ensembl_metadata

def get_ensembl_gtf_release_date(gtf_path):
    with open(gtf_path) as f:
        # Get first 5 lines, without reading file entirely into memory
        head = [next(f).strip() for x in range(5)]
    try:
        release_date = head[4].split('genebuild-last-updated ')[1]
    except IndexError:
        print('No annotation release date found for ' + gtf_path)
        return None
    return release_date


def get_ref_file_annot_metadata(organism_metadata):

    url = organism_metadata['annotation_url']
    index_url = organism_metadata['annotation_url']
    name = 'Ensembl ' + organism_metadata['release']

    gtf_path = organism_metadata['gtf_path'].replace('.gz', '')
    date = get_ensembl_gtf_release_date(gtf_path)

    return [name, date, url, index_url]


def update_meta_row(row, org_metadata, annot_metadata):
    """Update row from species_metadata_reference.tsv with annotation metadata
    """
    date = annot_metadata[1]

    ref_assembly_name = row[3]
    assembly_name = org_metadata['assembly_name']
    ref_assembly_acc = row[4]
    assembly_acc = org_metadata['assembly_accession']

    if ref_assembly_acc == assembly_acc or ref_assembly_name == assembly_name:
        if date is None:
            # If annotation is undated (as with Drosophila), use assembly date
            assembly_date = row[4]
            annot_metadata[1] = assembly_date
        new_row = '\t'.join(row + annot_metadata)
    else:
        new_row = '\t'.join(row)

    return new_row


def record_annotation_metadata(ensembl_metadata):
    """Adds annotation URLs, etc. to species metadata reference TSV file
    """
    new_metadata_ref = []

    ref_file = output_dir + 'species_metadata_reference.tsv'

    with open(ref_file) as f:
        metadata_ref = [line.strip().split('\t') for line in f.readlines()]

    for species in scp_species:
        taxid = species[2]
        org_metadata = ensembl_metadata[taxid]

        annot_metadata = get_ref_file_annot_metadata(org_metadata)

        for row in metadata_ref[1:]:
            ref_taxid = row[2]
            if taxid == ref_taxid:
                new_row = update_meta_row(row, org_metadata, annot_metadata)
                new_metadata_ref.append(new_row)

    assembly_headers = metadata_ref[0]
    annot_headers = [
        'annotation_name',
        'annotation_release_date',
        'annotation_url',
        'annotation_index_url'
    ]
    header = '\t'.join(assembly_headers + annot_headers) + '\n'
    new_metadata_ref = header + '\n'.join(new_metadata_ref)

    with open(ref_file, 'w') as f:
        f.write(new_metadata_ref)
    print('Wrote annotation metadata to ' + ref_file)

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
ensembl_metadata = upload_ensembl_gtf_products(ensembl_metadata)
record_annotation_metadata(ensembl_metadata)