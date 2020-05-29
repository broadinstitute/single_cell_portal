"""Parse genome assemblies from NCBI by their level of completion.

This script fetches current and historical Assembly Reports from NCBI, and
extracts metadata on assemblies that are relevant for Single Cell Portal.
See get_assembly_report docstring for more detail on historical Assembly
Reports.

Only assemblies that are chromosome-level or above are included.

For definitions of assembly-related terms and other domain background, see:
https://www.ncbi.nlm.nih.gov/assembly/help/#glossary
"""

import argparse
from functools import cmp_to_key
import os
import urllib.request as request

from utils import *

parser = argparse.ArgumentParser(
    description=__doc__, # Use docstring at top of file for --help summary
    formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument('--input_dir',
                    help='Input directory; where to find organisms.tsv.  Default: ./',
                    default='./')
parser.add_argument('--output_dir',
                    help='Directory to send output data to.  Default: output/',
                    default='output/')
args = parser.parse_args()
input_dir = args.input_dir
output_dir = args.output_dir

if os.path.exists(output_dir) is False:
    os.mkdir(output_dir)

species_list = get_species_list(input_dir + 'organisms.tsv')

# One-dimensional list of species names
species_names = [species[0] for species in species_list]


def get_assembly_report(use_historical=False):
    """ Fetch NCBI Assembly Report, or read it from disk if present

    :param use_historical {Boolean} Whether to use NCBI's historical Assembly 
      Report.  Needed to get major assembly versions when patches are available
      (e.g. human, mouse).
    """
    domain = 'https://ftp.ncbi.nlm.nih.gov'
    path = '/genomes/ASSEMBLY_REPORTS/'
    if use_historical:
        report_filename = 'assembly_summary_genbank_historical.txt'
    else:
        report_filename = 'assembly_summary_genbank.txt'
    assembly_report_url = domain + path + report_filename
    assembly_report_path = output_dir + report_filename

    # TODO: Refactor fetch_content so this is less gross.
    assembly_report = fetch_content([[assembly_report_url, assembly_report_path]])
    assembly_report = list(assembly_report.values())[0]

    return assembly_report


def parse_columns(columns):
    """ Extract relevant values from columns of the NCBI Assembly Report
    """
    accession = columns[0]
    refseq_category = columns[4]
    # taxid = columns[5]
    # species_taxid = columns[6] # Helps with dog, for example
    organism_name = columns[7]
    assembly_level = columns[11]
    release_type = columns[12]
    #genome_rep = columns[13]
    release_date = columns[14].replace('/', '-')
    assembly_name = columns[15]
    refseq_accession = columns[17]

    return [release_type, assembly_level, refseq_category, assembly_name, release_date,
            organism_name, accession, refseq_accession]


def is_relevant_assembly(rel_type, asm_level, refseq_category, refseq_acc):
    """ Determine if assembly is suitable for SCP
    """

    if (rel_type in 'Major' and asm_level == 'Chromosome') == False:
        # Exclude patch assemblies, and genomes that lack assembled chromosomes
        return False

    if refseq_category == 'na':
        # Encountered only in historical assembly report
        if refseq_acc == 'na':
            return False
    else:
        if refseq_category in ('representative genome', 'reference genome') == False:
            return False

    return True


def update_assemblies(columns, assemblies):
    """ Parse and return all relevant assemblies, by organism
    """
    (rel_type, asm_level, refseq_category, asm_name, rel_date, org_name,
        accession, refseq_acc) = parse_columns(columns)

    if is_relevant_assembly(rel_type, asm_level, refseq_category, refseq_acc):
        if org_name == 'Homo sapiens' and asm_name[:3] != 'GRC':
            # Omit CHM1_1.1, HuRef, etc.
            return assemblies
        assembly = [asm_name, accession, rel_date]
        if org_name not in assemblies:
            assemblies[org_name] = [assembly]
        else:
            assemblies[org_name].append(assembly)
    return assemblies


def refine_assemblies(assemblies):
    """ Filter assemblies to only those for relevant species; add species data
    """
    refined_assemblies = []

    for species in species_list:
        scientific_name, common_name, taxid = species
        if scientific_name not in assemblies:
            continue
        asms = assemblies[scientific_name]
        for asm in asms:
            (assembly_name, accession, release_date) = asm
            row = [scientific_name, common_name, taxid,
                assembly_name, accession, release_date]
            refined_assemblies.append(row)

    return refined_assemblies


def parse_assembly_report(assembly_report):
    """ Read Assembly Report, filter to relevant assemblies
    """
    assemblies = {}
    for line in assembly_report:
        if len(line) == 0 or line[0] == '#':
            # Skip header lines
            continue
        columns = line.split('\t')

        assemblies = update_assemblies(columns, assemblies)

    refined_assemblies = refine_assemblies(assemblies)

    return refined_assemblies


def write_assemblies_to_file(assemblies):
    """ Save assembly metadata to disk
    """
    assemblies_str = []
    header = ['# scientific_name', 'common_name', 'taxid',
        'assembly_name', 'assembly_accession', 'assembly_release_date']
    assemblies.insert(0, header)
    for assembly in assemblies:
        assemblies_str.append('\t'.join(assembly))
    assemblies_str = '\n'.join(assemblies_str)

    output_path = 'species_metadata_reference.tsv'
    with open(output_path, 'w') as f:
        f.write(assemblies_str)
    print('Wrote assemblies to ' + output_path)


def parse_genome_assemblies():
    """ Main method; fetch assembly reports and write filtered list to disk
    """

    assembly_report = get_assembly_report()
    historical_assembly_report = get_assembly_report(use_historical=True)

    assemblies = parse_assembly_report(assembly_report)
    historical_assemblies = parse_assembly_report(historical_assembly_report)

    assemblies += historical_assemblies

    # Sort assemblies by species priority and assembly release date
    assemblies = sorted(
        assemblies, key=lambda assembly: assembly[4], reverse=True)
    assemblies = sorted(
        assemblies, key=lambda assembly: species_names.index(assembly[0]))

    write_assemblies_to_file(assemblies)


parse_genome_assemblies()
