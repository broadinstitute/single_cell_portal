"""Pipeline to download, transform, and upload genome reference data for SCP

SUMMARY

This ETL pipeline downloads, transforms, and uploads reference data for
genome assemblies and genome annotations needed for Single Cell Portal (SCP).

Raw data is fetched from NCBI and Ensembl, processed to transform it as needed,
then uploaded to a Google Cloud Storage (GCS) bucket for SCP.  The uploaded data
is used to display interactive genome visualizations, e.g. igv.js and
Ideogram.js, and (in the future) to run biological workflows / analysis
pipelines, e.g. Cell Ranger and inferCNV.

To use this reference data in SCP, upload the "species_reference_metadata.tsv"
file in the "outputs" directory using the "Upload Species List" button in
https://portals.broadinstitute.org/single_cell/species.

INSTALL

python3 -m venv env
source env/bin/activate
pip3 install -r requirements.txt

EXAMPLES

# Basic usage.  Upload GTF products to reference_dev in default SCP GCS bucket.
$ python3 process_genome_references.py --vault-path=secrets/service_account.json --input-dir ../../../lib/assets/python/genomes/

# Upload GTF products to reference_data_staging folder, using cached data from previous run
$ python3 process_genome_references.py --vault-path=secrets/service_account.json --input-dir ../../../lib/assets/python/genomes/ --remote-output-dir reference_data_staging/ --use-cache

TODO (SCP-2470): Move /scripts/genomes (including this module) to scp-ingest-pipeline
"""

# This script is basically a wrapper for:
#   parse_genome_assemblies.py
#   parse_genome_annotations.py

import argparse
import subprocess

parser = argparse.ArgumentParser(
    description=__doc__, # Use docstring at top of file for --help summary
    formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument('--vault-path',
                    help='Path in Vault for GCS service account credentials')
parser.add_argument('--input-dir',
                    help='Input directory; where to find organisms.tsv.  Default: ./',
                    default='./')
parser.add_argument('--remote-output-dir',
                    help='Remote directory for output in GCS bucket.  ' +
                    'Default: reference_data_dev/',
                    default='reference_data_dev/')
parser.add_argument('--local-output-dir',
                    help='Local directory for output.  Default: output/',
                    default='output/')
parser.add_argument('--gcs-bucket',
                    help='Name of GCS bucket for upload.  ' +
                    'Default: reference_data_dev/',
                    default='fc-bcc55e6c-bec3-4b2e-9fb2-5e1526ddfcd2')
parser.add_argument('--copy-data-from-prod-dir',
                    help='Remote directory from which to copy data into ' +
                    'remote_output_dir.  Use to ensure test data ' +
                    'environment is equivalent to production data ' +
                    'environment.  Default: reference_data/',
                    default='reference_data/')
parser.add_argument('--use-cache',
                    help='Whether to use cache',
                    action='store_true')
args = parser.parse_args()

vault_path = args.vault_path
input_dir = args.input_dir
remote_output_dir = args.remote_output_dir
local_output_dir = args.local_output_dir
gcs_bucket = args.gcs_bucket
copy_data_from_prod_dir = args.copy_data_from_prod_dir
use_cache = args.use_cache

# Call downstream scripts
# TODO: enable scripts to be used as modules
assemblies_command = ['python3', 'parse_genome_assemblies.py']
print('Calling ' + ' '.join(assemblies_command))
subprocess.call(assemblies_command)
annotations_command = [
    'python3', 'parse_genome_annotations.py',
    '--vault_path', vault_path,
    '--input_dir', input_dir,
    '--remote_output_dir', remote_output_dir,
    '--local_output_dir', local_output_dir,
    '--gcs_bucket', gcs_bucket,
    '--copy_data_from_prod_dir', copy_data_from_prod_dir
]
if use_cache:
    annotations_command.append('--use_cache')
print('Calling ' + ' '.join(annotations_command))
subprocess.call(annotations_command)
