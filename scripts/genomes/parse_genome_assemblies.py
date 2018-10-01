""" Parse genome assemblies from NCBI by their level of completion
"""

import argparse
import urllib.request as request
import os

parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument('--output_dir',
    help='Directory to sent output data to',
    default='output/')
args = parser.parse_args()
output_dir = args.output_dir

if os.path.exists(output_dir) is False:
    os.mkdir(output_dir)

def get_assembly_report():
  """ Fetch NCBI Assembly Report, or read it from disk if present
  """
  domain = 'https://ftp.ncbi.nlm.nih.gov'
  path = '/genomes/ASSEMBLY_REPORTS/'
  report_filename = 'assembly_summary_genbank.txt'
  ncbi_assembly_report_url = domain + path + report_filename
  ncbi_assembly_report_path = output_dir + report_filename

  if os.path.exists(ncbi_assembly_report_path):
    # Use local report if available
    with open(ncbi_assembly_report_path) as f:
      assembly_report = f.readlines()
  else:
    # If local report absent, fetch assembly report and cache it
    with request.urlopen(ncbi_assembly_report_url) as response:
      assembly_data = response.read().decode('utf-8')
      with open(ncbi_assembly_report_path, 'w') as f:
        f.write(assembly_data)
      assembly_report = assembly_data.split('\n')
  print('Fetched NCBI Assembly Report')

  return assembly_report

def parse_columns(columns):
  """ Retrieve relevant values from columns of the NCBI Assembly Report
  """
  # accession = columns[0]
  # refseq_category = columns[4]
  # taxid = columns[5]
  # species_taxid = columns[6] # Helps with dog, for example
  organism_name = columns[7]
  assembly_level = columns[11]
  release_type = columns[12]
  #genome_rep = columns[13]
  release_date = columns[14]
  assembly_name = columns[15]

  return [release_type, assembly_level, assembly_name, release_date,
    organism_name]

def update_assemblies(rel_type, asm_level, asm_name, rel_date, org_name, assemblies):
  """ Parse and return all relevant assemblies, by organism
  """
  if rel_type == 'Major' and asm_level == 'Chromosome':
      assembly = [asm_name, rel_date]
      if org_name not in assemblies:
        assemblies[org_name] = [assembly]
      else:
        assemblies[org_name].append(assembly)
  return assemblies

def parse_genome_assemblies():

  assemblies = {}

  assembly_report = get_assembly_report()

  for line in assembly_report:
    if line[0] == '#':
      # Skip header lines
      continue
    columns = line.split('\t')

    rel_type, asm_level, asm_name, rel_date, org_name = parse_columns(columns)

    assemblies = update_assemblies(rel_type, asm_level, asm_name, rel_date,
      org_name, assemblies)

  num_organisms = len(assemblies.keys())
  print('Organisms with relevant assemblies: ' + str(num_organisms))

parse_genome_assemblies()