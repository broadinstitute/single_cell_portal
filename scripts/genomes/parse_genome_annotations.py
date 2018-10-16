"""Parse genome annotations, output position-sorted GTF in plaintext and compressed
"""

import json
import urllib.request as request
import subprocess

from utils import *

output_dir = 'output/'
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
    """ Construct the URL of an Ensembl genome annotation GTF file.

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

    return gtf_urls

def write_ensembl_gtf_products(ensembl_metadata):
    """ Downloads Ensembl GTFs, produces position-sorted raw and indexed GTFs
    """
    gtf_urls = get_ensembl_gtf_urls(ensembl_metadata)
    gtfs = batch_fetch(gtf_urls, output_dir)
    print('Got GTFs!  Number: ' + str(len(gtfs)))
    for gtf in gtfs:
        # $ sort -k1,1 -k4,4n gencode.vM17.annotation.gtf > gencode.vM17.annotation.possorted.gtf
        # $ bgzip gencode.vM17.annotation.possorted.gtf
        # $ tabix -p gff gencode.vM17.annotation.possorted.gtf.gz
        output_path = gtf[0].replace('.gz', '')
        sort_command = ('sort -k1,1 -k4,4n ' + output_path).split(' ')
        sorted_filename = output_path.replace('.gtf', '.possorted.gtf')
        sorted_file = open(sorted_filename, 'w')
        print('Running ' + str(sort_command))
        subprocess.call(sort_command, stdout=sorted_file)
        bgzip_command = ('bgzip ' + sorted_filename).split(' ')
        print('Running ' + str(bgzip_command))
        subprocess.call(bgzip_command)
        tabix_command = ('tabix -p gff ' + sorted_filename + '.gz').split(' ')
        print('Running ' + str(tabix_command))
        subprocess.call(tabix_command)

ensembl_metadata = get_ensembl_metadata()
gtfs = get_ensembl_gtfs(ensembl_metadata)
print('gtfs')
print(len(gtfs))
