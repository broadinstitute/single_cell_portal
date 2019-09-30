#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""Command-line interface for managing studies in Single Cell Portal (SCP)

DESCRIPTION
This CLI exposes SCP functionality via several subparsers, e.g. "list-study",
"upload-study".  You can invoke this functionality by passing a subparser name
into your command-line call, as shown in the EXAMPLES section below.

PREREQUISITES
To use this tool, you must have Google Cloud SDK installed and initialized.
See https://cloud.google.com/sdk/docs/ for details.

See https://github.com/broadinstitute/single_cell_portal#convenience-scripts
for other requirements.

EXAMPLES
# First, sign in and assign access token
gcloud auth login
ACCESS_TOKEN=`gcloud auth print-access-token`

# List studies in SCP
python manage_study.py list-studies

# Get number of studies in SCP, using token to bypass browser log-in
python manage_study.py --token=$ACCESS_TOKEN list-studies --summary

# Get help for "create-study"
python manage_study.py create-study --help

# Create a study named "CLI test"
python3 manage_study.py --token=$ACCESS_TOKEN create-study --study-name "CLI test"
"""

import argparse
import json
import os

import Commandline
import scp_api

import ingest
from ingest.cell_metadata import CellMetadata
from ingest.validation.validate_metadata import (
    collect_jsonschema_errors,
    validate_collected_ontology_data,
    report_issues,
    serialize_issues,
    exit_if_errors
)

# Subparser tool names
c_TOOL_LIST_STUDY = "list-studies"
c_TOOL_CLUSTER = "upload-cluster"
c_TOOL_EXPRESSION = "upload-expression"
c_TOOL_METADATA = "upload-metadata"
c_TOOL_PERMISSION = "permission"
c_TOOL_STUDY = "create-study"

def manage_call_return(call_return, verbose=False):
    '''
    Accesses the error codes in the underlying library and check the return code.

    :param call_return: Dict returned from scp_api call with REST call return info
    :return: No return will exit on error
    '''
    # Print error code and describe code then exit if not success
    if verbose:
        print("HTTP status code = " + str(call_return[scp_api.c_CODE_RET_KEY]))
        print(scp_api.SCPAPIManager.describe_status_code(call_return[scp_api.c_CODE_RET_KEY]))
    if not call_return[scp_api.c_SUCCESS_RET_KEY]:
        exit(call_return[scp_api.c_CODE_RET_KEY])

def succeeded(ret):
    """Whether request succeeded
    """
    # 2xx, e.g. 200 or 204, means success
    return str(ret['response'].status_code)[0] == '2'

def login(manager=None, dry_run=False, api_base=None, verbose=False):
    '''
    Login to authorize credentials.

    :param manager: API Manager
    :param dry_run: If true, will do a dry run with no actual execution of functionality.
    :return:
    '''
    if manager is None:
        manager=scp_api.SCPAPIManager(verbose=verbose)
        manager.login(token=parsed_args.token,
                      dry_run=dry_run,
                      api_base=api_base)
    return(manager)

def validate_metadata_file(convention_path, metadata_path):
    with open(convention_path) as f:
        convention = json.load(f)
    metadata = CellMetadata(metadata_path, '', '')
    print(f'Validating {metadata_path}')
    format_valid = metadata.validate_format()
    collect_jsonschema_errors(metadata, convention)
    validate_collected_ontology_data(metadata, convention)
    serialize_issues(metadata)
    report_issues(metadata)
    exit_if_errors(metadata)

args = argparse.ArgumentParser(
    prog='manage_study.py',
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter
)
args.add_argument(
    '--token', dest='token', default=None,
    help='Personal token after logging into Google (OAuth2).  This token is not persisted after the finish of the script.'
)
args.add_argument(
    '--dry_run', dest='dry_run', action='store_true',
    help='Walk through and log what would occur, without performing the actions.'
)
args.add_argument(
    '--no-validate', dest='validate',
    action='store_false',
    help='Do not check file locally before uploading.'
)
args.add_argument(
    '--verbose',
    action='store_true',
    help='Whether to print debugging information'
)

args.add_argument(
    '--environment', default='production',
    choices=['development', 'production'],
    help='API environment to use'
)

# Create tools (subparser)
subargs = args.add_subparsers()

## List studies subparser
parser_list_studies = subargs.add_parser(c_TOOL_LIST_STUDY,
    help="List studies. \""+args.prog+" "+c_TOOL_LIST_STUDY+" -h\" for more details")
parser_list_studies.add_argument(
    '--summary', dest='summarize_list', action='store_true',
    help='Do not list, only summarize number of accessible studies'
)

## Create study subparser
parser_create_studies = subargs.add_parser(c_TOOL_STUDY,
    help="Create a study. \""+args.prog+" "+c_TOOL_STUDY+" -h\" for more details")
parser_create_studies.add_argument(
    '--description', dest='study_description',
    default="Single Cell Genomics Study",
    help='Short description of the study'
)
parser_create_studies.add_argument(
    '--study-name', dest='study_name', required=True,
    help='Short name of the study'
)
parser_create_studies.add_argument(
    '--branding', dest='branding', default=None,
    help='Portal branding to associate with the study'
)
parser_create_studies.add_argument(
    '--billing', default=None,
    help='Portal billing project to associate with the study'
)
parser_create_studies.add_argument(
    '--is-private', action='store_true',
    help='Whether the study is private'
)

## Permissions subparser
parser_permissions = subargs.add_parser(c_TOOL_PERMISSION,
    help="Change user permissions in a study. \""+args.prog+" "+c_TOOL_PERMISSION+" -h\" for more details")
parser_permissions.add_argument(
    '--email', dest='email', required=True,
    default='Single Cell Genomics Study',
    help='User email to update study permission.'
)
parser_permissions.add_argument(
    '--study-name', dest='study_name', required=True,
    help='Short name of the study.'
)
parser_permissions.add_argument(
    '--access', dest='permission', choices=scp_api.c_PERMISSIONS, required=True,
    help='Access to give the user.  Must be one of the following values: '+" ".join(scp_api.c_PERMISSIONS)
)

## Create cluster file upload subparser
parser_upload_cluster = subargs.add_parser(c_TOOL_CLUSTER,
    help="Upload a cluster file. \""+args.prog+" "+c_TOOL_CLUSTER+" -h\" for more details")
parser_upload_cluster.add_argument(
    '--file', dest='cluster_file', required=True,
    help='Cluster file to load.'
)
parser_upload_cluster.add_argument(
    '--study-name', dest='study_name', required=True,
    help='Name of the study to add the file.'
)
parser_upload_cluster.add_argument(
    '--description', dest='description',
    default="Coordinates and optional metadata to visualize clusters.",
    help='Text describing the cluster file.'
)
parser_upload_cluster.add_argument(
    '--cluster-name', dest='cluster_name', required=True,
    help='Name of the clustering that will be used to refer to the plot.'
)
parser_upload_cluster.add_argument(
    '--x', dest='x_label',
    default=None,
    help='X axis label (test).'
)
parser_upload_cluster.add_argument(
    '--y', dest='y_label',
    default=None,
    help='Y axis label (test).'
)
parser_upload_cluster.add_argument(
    '--z', dest='z_label',
    default=None,
    help='Z axis label (test).'
)

## Create expression file upload subparser
parser_upload_expression = subargs.add_parser(c_TOOL_EXPRESSION,
    help="Upload a gene expression matrix file. \""+args.prog+" "+c_TOOL_EXPRESSION+" -h\" for more details")
parser_upload_expression.add_argument(
    '--file', dest='expression_file', required=True,
    help='Expression file to load.'
)
parser_upload_expression.add_argument(
    '--study-name', dest='study_name', required=True,
    help='Name of the study to add the file.'
)
parser_upload_expression.add_argument(
    '--description', dest='description',
    default='Gene expression in cells',
    help='Text describing the gene expression matrix file.'
)
parser_upload_expression.add_argument(
    '--species', dest='species', required=True,
    help='Species from which the data is generated.'
)
parser_upload_expression.add_argument(
    '--genome', dest='genome', required=True,
    help='Genome assembly used to generate the data.'
)
# TODO: Add upstream support for this in SCP RESI API
# parser_upload_expression.add_argument(
#     '--axis_label', dest='axis_label',
#     default='',
#     help=''
# )

## Create metadata file upload subparser
parser_upload_metadata = subargs.add_parser(c_TOOL_METADATA,
    help="Upload a metadata file. \""+args.prog+" "+c_TOOL_METADATA+" -h\" for more details")
parser_upload_metadata.add_argument(
    '--file', dest='metadata_file', required=True,
    help='Metadata file to load.'
)
parser_upload_metadata.add_argument(
    '--convention',
    help='Metadata convention JSON file '
)
parser_upload_metadata.add_argument(
    '--study-name', dest='study_name', required=True,
    help='Name of the study to add the file.'
)
parser_upload_metadata.add_argument(
    '--description', dest='description',
    default='',
    help='Text describing the metadata file.'
)

parsed_args = args.parse_args()
if parsed_args.verbose:
    print("Args----")
    print(vars(parsed_args))
    print("-----Args")

verbose = parsed_args.verbose

env_origin_map = {
    'development': 'https://localhost',
    'production': 'https://singlecell.broadinstitute.org'
}
origin = env_origin_map[parsed_args.environment]
api_base = origin + '/single_cell/api/v1/'

if __name__ == '__main__':
    # Login connection
    connection = login(manager=None, dry_run=parsed_args.dry_run, api_base=api_base, verbose=verbose)

    ## Handle list studies
    if hasattr(parsed_args, "summarize_list"):
        if verbose: print("START LIST STUDIES")
        ret = connection.get_studies(dry_run=parsed_args.dry_run)
        manage_call_return(ret)
        print("You have access to "+str(len(ret[scp_api.c_STUDIES_RET_KEY]))+" studies.")
        if not parsed_args.summarize_list:
            print(os.linesep.join(ret[scp_api.c_STUDIES_RET_KEY]))

    ## Create new study
    if hasattr(parsed_args, "study_description") and not parsed_args.study_name is None:
        if verbose: print("START CREATE STUDY")
        is_public = not parsed_args.is_private
        ret = connection.create_study(study_name=parsed_args.study_name,
                                    study_description=parsed_args.study_description,
                                    branding=parsed_args.branding,
                                    billing=parsed_args.billing,
                                    is_public=is_public,
                                    dry_run=parsed_args.dry_run)
        manage_call_return(ret)
        if succeeded(ret):
            print('Created study')

    ## Share with user
    if hasattr(parsed_args, "permission"):
        if verbose: print("START SET PERMISSION")
        ret = connection.set_permission(study_name=parsed_args.study_name,
                                        email=parsed_args.email,
                                        access=parsed_args.permission,
                                        dry_run=parsed_args.dry_run)
        manage_call_return(ret)
        if succeeded(ret):
            print('Set permission')

    ## Validate files
    if parsed_args.validate and not hasattr(parsed_args, "summarize_list"):

        if verbose: print("START VALIDATE FILES")

        if hasattr(parsed_args, "metadata_file"):
            convention_path = parsed_args.convention
            validate_metadata_file(convention_path, parsed_args.metadata_file)

        # command = ["python3 verify_portal_file.py"]

        # if hasattr(parsed_args, "cluster_file"):
        #     command.extend(["--coordinates-file", parsed_args.cluster_file])
        # if hasattr(parsed_args, "expression_file"):
        #     command.extend(["--expression-files", parsed_args.expression_file])
        # if hasattr(parsed_args, "metadata_file"):
        #     command.extend(["--metadata-file", parsed_args.metadata_file])

        # if parsed_args.dry_run:
        #     print("TESTING:: no command executed."+os.linesep+"Would have executed: " + os.linesep + " ".join(command))
        # else:
        #     valid_code = Commandline.Commandline().func_CMD(" ".join(command))
        #     if verbose: print(valid_code)
        #     if not valid_code:
        #         print("There was an error validating the files, did not upload. Code=" + str(valid_code))
        #         exit(valid_code)

    ## Upload cluster file
    if hasattr(parsed_args, "cluster_file"):
        if verbose: print("START UPLOAD CLUSTER FILE")
        connection = login(manager=connection, dry_run=parsed_args.dry_run)
        ret = connection.upload_cluster(file=parsed_args.cluster_file,
                                        study_name=parsed_args.study_name,
                                        cluster_name=parsed_args.cluster_name,
                                        description=parsed_args.description,
                                        x=parsed_args.x_label,
                                        y=parsed_args.y_label,
                                        z=parsed_args.z_label,
                                        dry_run=parsed_args.dry_run)
        manage_call_return(ret)
        if succeeded(ret):
            print('Uploaded and began parse of cluster file')

    ## Upload metadata file
    if hasattr(parsed_args, "metadata_file"):
        if verbose: print("START UPLOAD METADATA FILE")
        connection = login(manager=connection, dry_run=parsed_args.dry_run)
        ret = connection.upload_metadata(file=parsed_args.metadata_file,
                                        study_name=parsed_args.study_name,
                                        dry_run=parsed_args.dry_run)
        manage_call_return(ret)
        if succeeded(ret):
            print('Uploaded and began parse of metadata file')

    ## Upload expression file
    if hasattr(parsed_args, "expression_file"):
        if verbose: print("START UPLOAD EXPRESSION FILE")
        connection = login(manager=connection, dry_run=parsed_args.dry_run)
        ret = connection.upload_expression_matrix(file=parsed_args.expression_file,
                                        study_name=parsed_args.study_name,
                                        species=parsed_args.species,
                                        genome=parsed_args.genome,
                                        dry_run=parsed_args.dry_run)
        manage_call_return(ret)
        if succeeded(ret):
            print('Uploaded and began parse of expression file')

    ## Upload miscellaneous file
    ### TODO

    ## Validate and Upload and Sort 10X files
    ### TODO

    ## Validate and Upload 10X directory
    ### TODO

    ## Validate and Upload fastqs
    ### TODO

    ## Validate and Upload bams
    ### TODO

