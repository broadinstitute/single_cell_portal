"""Parse genome annotations, output position-sorted GTF in plaintext and compressed
"""

import json
import urllib.request as request

from utils import *

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
        releases_by_taxid[taxid] = {
            'organism': species['name'],
            'taxid': species['taxid'],
            'assembly_name': species['assembly'],
            'assembly_accession': species['accession'],
            'release': species['release']
        }

    return ensembl_metadata

def get_ensembl_gtf_url(organism_metadata):
    """ Construct the URL of an Ensembl genome annotation GTF file.

    Example URL:
    http://ftp.ensembl.org/pub/release-94/gtf/homo_sapiens/Homo_sapiens.GRCh38.94.gtf.gz
    """

    release = organism_metadata['release']
    organism = organism_metadata['organism']
    organism_upper = organism[0].upper() + organism[1:]

    origin = 'http://ftp.ensembl.org'
    dir = '/pub/release' + release + '/gtf/' + organism + '/'
    filename = organism_upper + '.' + assembly_name + 'gtf.gz'

    gtf_url = origin + dir + filename
    return gtf_url


def get_ensembl_gtf(organism_metadata):
    gtf_url = get_ensembl_gtf_url(organism_metadata)

    return


ensembl_metadata = get_ensembl_metadata()

for species in scp_species:
    taxid = species[2]
    organism_metadata = ensembl_metadata[taxid]
    gtf = get_ensembl_gtf(organism_metadata)
