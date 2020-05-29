"""Download genome annotations, transform for visualizations, upload to GCS
"""

import argparse
import json
import os
import shutil
import subprocess
import urllib.request as request

from persist_annotation_metadata import *
from utils import *

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

def get_ensembl_gtf_urls(ensembl_metadata, scp_species, output_dir):
    """Construct the URL of an Ensembl genome annotation GTF file.

    Example URL:
    http://ftp.ensembl.org/pub/release-94/gtf/homo_sapiens/Homo_sapiens.GRCh38.94.gtf.gz
    """

    gtf_urls = []
    for species in scp_species:
        taxid = species[2]
        print('scp_species')
        print(scp_species)
        print('taxid')
        print(taxid)
        print('ensembl_metadata')
        print(ensembl_metadata)
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

def make_local_reference_dirs(ensembl_metadata, scp_species):
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

def fetch_gtfs(scp_species, output_dir='.', ensembl_metadata=None):
    """Request GTF files, return their contents and updated Ensembl metadata
    """
    if ensembl_metadata is None:
        ensembl_metadata = get_ensembl_metadata()

    gtf_urls, ensembl_metadata = get_ensembl_gtf_urls(ensembl_metadata, scp_species, output_dir)

    print('Fetching GTFs')
    gtfs = batch_fetch(gtf_urls, output_dir)
    print('Got GTFs!  Number: ' + str(len(gtfs)))

    return gtfs, ensembl_metadata


def transform_ensembl_gtfs(ensembl_metadata, scp_species, output_dir):
    """Download raw Ensembl GTFs, write position-sorted GTF and index
    """
    transformed_gtfs = []

    gtfs, ensembl_metadata = fetch_gtfs(scp_species, output_dir=output_dir, ensembl_metadata=ensembl_metadata)

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

def create_parser():
    """Creates parser for input arguments.
    Structuring the argument parsing code like this eases automated testing.

    Args:
        None
    Returns:
        parser: ArgumentParser object
    """
    parser = argparse.ArgumentParser(
    description=__doc__, # Use docstring at top of file for --help summary
    formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--use_cache',
                        help='Whether to use cache',
                        action='store_true')
    parser.add_argument('--vault_path',
                        help='Path in Vault for GCS service account credentials')
    parser.add_argument('--input_dir',
                        help='Input directory; where to find organisms.tsv.  Default: ./',
                        default='./')
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

    return parser

def main():
    """Enables running this module via CLI
    """
    args = create_parser().parse_args()

    use_cache = args.use_cache
    vault_path = args.vault_path
    input_dir = args.input_dir
    output_dir = args.local_output_dir
    gcs_bucket = args.gcs_bucket
    remote_prod_dir = args.copy_data_from_prod_dir
    remote_output_dir = args.remote_output_dir

    scp_species = get_species_list(input_dir + 'organisms.tsv')

    context = {
        'vault_path': vault_path,
        'gcs_bucket': gcs_bucket,
        'output_dir': output_dir,
        'remote_prod_dir': remote_prod_dir,
        'remote_output_dir': remote_output_dir
    }

    ensembl_metadata = get_ensembl_metadata()
    ensembl_metadata = transform_ensembl_gtfs(ensembl_metadata, scp_species, output_dir)
    ensembl_metadata = upload_ensembl_gtf_products(ensembl_metadata, scp_species, context)
    record_annotation_metadata(ensembl_metadata, scp_species)
