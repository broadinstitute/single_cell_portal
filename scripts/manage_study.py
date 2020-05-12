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

# Upload an expression matrix
python3 manage_study.py --token=$ACCESS_TOKEN upload-expression --file ../demo_data/expression_example.txt --study-name "CLI test" --species "human" --genome "GRCh38"

# Upload a metadata file (without validating against the metadata convention)
python3 manage_study.py --token=$ACCESS_TOKEN upload-metadata --study-name "CLI test" --file ../demo_data/metadata_example.txt

# Upload a cluster file
python3 manage_study.py --token=$ACCESS_TOKEN upload-cluster --study-name "${STUDY_NAME}" --file ../demo_data/cluster_example.txt  --cluster-name 'Test cluster' --description test

# Edit study description
python3 manage_study.py --token-$ACCESS_TOKEN edit-study-description --study-name "${STUDY_NAME}" --new-description "This is a test."

# Create an external resource
python3 manage_study.py --token-$ACCESS_TOKEN create-study-external-resource --study-name "${STUDY_NAME}" --title "External_Link" \
--url "https://singlecell.broadinstitute.org/single_cell" --description "This sends you home."

# Print a study attribute (eg. cell_count)
python3 manage_study.py --token-$ACCESS_TOKEN get-study-attribute --study-name "${STUDY_NAME}" --attribute cell_count
"""

import argparse
import json
import os

from google.cloud import storage
from ingest.ingest_pipeline import IngestPipeline
from ingest.cell_metadata import CellMetadata
from ingest.validation.validate_metadata import (
    report_issues,
    serialize_issues,
    exit_if_errors,
    validate_input_metadata,
)

import Commandline
import scp_api

# Subparser tool names
c_TOOL_LIST_STUDY = "list-studies"
c_TOOL_CLUSTER = "upload-cluster"
c_TOOL_EXPRESSION = "upload-expression"
c_TOOL_METADATA = "upload-metadata"
c_TOOL_PERMISSION = "permission"
c_TOOL_STUDY = "create-study"
c_TOOL_STUDY_EDIT_DESC= "edit-study-description"
c_TOOL_STUDY_GET_ATTR= "get-study-attribute"
c_TOOL_STUDY_GET_EXT= 'get-study-external-resources'
c_TOOL_STUDY_DEL_EXT= 'delete-study-external-resources'
c_TOOL_STUDY_CREATE_EXT = 'create-study-external-resource'


def manage_call_return(call_return, verbose=False):
    '''
    Accesses the error codes in the underlying library and check the return code.

    :param call_return: Dict returned from scp_api call with REST call return info
    :return: No return will exit on error
    '''
    # Print error code and describe code then exit if not success
    if verbose:
        print("HTTP status code = " + str(call_return[scp_api.c_CODE_RET_KEY]))
        print(
            scp_api.SCPAPIManager.describe_status_code(
                call_return[scp_api.c_CODE_RET_KEY]
            )
        )
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
        manager = scp_api.SCPAPIManager(verbose=verbose)
        manager.login(token=parsed_args.token, dry_run=dry_run, api_base=api_base)
    return manager

def download_from_bucket(file_path):
    """Downloads file from Google Cloud Storage bucket"""

    path_segments = file_path[5:].split("/")

    storage_client = storage.Client()
    bucket_name = path_segments[0]
    bucket = storage_client.get_bucket(bucket_name)
    source = "/".join(path_segments[1:])

    blob = bucket.blob(source)
    destination = "/tmp/" + source.replace("/", "%2f")
    blob.download_to_filename(destination)
    print(f"{file_path} downloaded to {destination}.")

    return destination

def validate_metadata_file(metadata_path):
    study_accession_res =connection.get_study_attribute(
        study_name=parsed_args.study_name,
        attribute='accession',
        dry_run=parsed_args.dry_run)
    print(study_accession_res)
    if succeeded(study_accession_res):
        if verbose:
            print(f'Study accession {study_accession_res} retrieved for {parsed_args.study_name}')
        study_accession = study_accession_res.get('study_attribute')
        metadata = CellMetadata(metadata_path, '', '', study_accession=str(study_accession))
        convention_res = connection.do_get(command=api_base + 'metadata_schemas/alexandria_convention/latest/json',dry_run=parsed_args.dry_run)
        if succeeded(convention_res ):
            if verbose:
                print(f'Retreieved file for latest metdata convention')
            convention = convention_res["response"].json()
            validate_input_metadata(metadata, convention)
            serialize_issues(metadata)
            report_issues(metadata)
            exit_if_errors(metadata)

def confirm(question):
    while True:
        answer = input(question + ' (y/n): ').lower().strip()
        if answer in ('y', 'yes', 'n', 'no'):
            return answer in ('y', 'yes')

args = argparse.ArgumentParser(
    prog='manage_study.py',
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
args.add_argument(
    '--token',
    default=None,
    help='Personal token after logging into Google (OAuth2).  This token is not persisted after the finish of the script.',
)
args.add_argument(
    '--dry-run',
    action='store_true',
    help='Walk through and log what would occur, without performing the actions.',
)
args.add_argument(
    '--no-validate',
    dest='validate',
    action='store_false',
    help='Do not check file locally before uploading.',
)
args.add_argument(
    '--verbose', action='store_true', help='Whether to print debugging information'
)

args.add_argument(
    '--environment',
    default='production',
    choices=['development', 'staging', 'production'],
    help='API environment to use',
)


# Create tools (subparser)
subargs = args.add_subparsers(dest = 'command')

## List studies subparser
parser_list_studies = subargs.add_parser(
    c_TOOL_LIST_STUDY,
    help="List studies. \""
    + args.prog
    + " "
    + c_TOOL_LIST_STUDY
    + " -h\" for more details",
)
parser_list_studies.add_argument(
    '--summary',
    dest='summarize_list',
    action='store_true',
    help='Do not list, only summarize number of accessible studies',
)

## Create study subparser
parser_create_studies = subargs.add_parser(
    c_TOOL_STUDY,
    help="Create a study. \""
    + args.prog
    + " "
    + c_TOOL_STUDY
    + " -h\" for more details",
)
parser_create_studies.add_argument(
    '--description',
    dest='study_description',
    default="Single Cell Genomics Study",
    help='Short description of the study',
)
parser_create_studies.add_argument(
    '--study-name', required=True, help='Short name of the study'
)
parser_create_studies.add_argument(
    '--branding',
    default=None,
    help='Portal branding to associate with the study',
)
parser_create_studies.add_argument(
    '--billing', default=None, help='Portal billing project to associate with the study'
)
parser_create_studies.add_argument(
    '--is-private', action='store_true', help='Whether the study is private'
)

# Create edit description subparser
parser_edit_description = subargs.add_parser(
    c_TOOL_STUDY_EDIT_DESC,
    help="Edit a study description. \""
    + args.prog
    + " "
    + c_TOOL_STUDY_EDIT_DESC
    + " -h\" for more details",
)
parser_edit_description.add_argument(
    '--study-name',
    required=True,
    help='Name of the study for which to edit description.',
)
parser_edit_description.add_argument(
    '--new-description',
    required=True,
    help='New description of the study to replace current one.',
)

parser_edit_description.add_argument(
    '--from-file',
    action='store_true',
    help='If true, assumes new_description argument is name pointing to file containing new_description.',
)

parser_edit_description.add_argument(
    '--accept-html',
    action='store_true',
    help='If true, will allow HTML formatting in new description.',
)

## Create study get attribute subparser
parser_get_attribute = subargs.add_parser(
    c_TOOL_STUDY_GET_ATTR,
    help="Get a study attribute (such as cell_count, etc). \""
    + args.prog
    + " "
    + c_TOOL_STUDY_GET_ATTR
    + " -h\" for more details",
)
parser_get_attribute.add_argument(
    '--study-name',
    required=True,
    help='Name of the study from which to get attribute.',
)
parser_get_attribute.add_argument(
    '--attribute',
    required=True,
    help='Attribute to return (such as cell_count, etc).',
)

## Create study get external resources subparser
parser_get_ext_resources = subargs.add_parser(
    c_TOOL_STUDY_GET_EXT,
    help="Get study external resources for a study. \""
    + args.prog
    + " "
    + c_TOOL_STUDY_GET_EXT
    + " -h\" for more details",
)
parser_get_ext_resources.add_argument(
    '--study-name',
    required=True,
    help='Name of the study from which to get resources.',
)

## Create study delete external resources subparser
parser_delete_ext_resources = subargs.add_parser(
    c_TOOL_STUDY_DEL_EXT,
    help="Delete all study external resources for a study. \""
    + args.prog
    + " "
    + c_TOOL_STUDY_DEL_EXT
    + " -h\" for more details",
)
parser_delete_ext_resources.add_argument(
    '--study-name',
    required=True,
    help='Name of the study from which to delete resources.',
)

## Create study new external resource subparser
parser_create_ext_resource = subargs.add_parser(
    c_TOOL_STUDY_CREATE_EXT,
    help="Create a new external resource for a study. \""
    + args.prog
    + " "
    + c_TOOL_STUDY_CREATE_EXT
    + " -h\" for more details",
)
parser_create_ext_resource.add_argument(
    '--study-name',
    required=True,
    help='Name of the study to which to add resource.',
)
parser_create_ext_resource.add_argument(
    '--title',
    required=True,
    help='Title of resource.',
)
parser_create_ext_resource.add_argument(
    '--url',
    required=True,
    help='URL of resource.',
)
parser_create_ext_resource.add_argument(
    '--description',
    required=True,
    help='Tooltip description of resource.',
)
parser_create_ext_resource.add_argument(
    '--publication-url',
    action='store_true',
    help='Whether resource is publication URL.',
)
# TODO: Fix permissions subparser (SCP-2024)
# ## Permissions subparser
# parser_permissions = subargs.add_parser(
#     c_TOOL_PERMISSION,
#     help="Change user permissions in a study. \""
#     + args.prog
#     + " "
#     + c_TOOL_PERMISSION
#     + " -h\" for more details",
# )
# parser_permissions.add_argument(
#     '--email',
#     dest='email',
#     required=True,
#     default='Single Cell Genomics Study',
#     help='User email to update study permission.',
# )
# parser_permissions.add_argument(
#     '--study-name', dest='study_name', required=True, help='Short name of the study.'
# )
# parser_permissions.add_argument(
#     '--access',
#     dest='permission',
#     choices=scp_api.c_PERMISSIONS,
#     required=True,
#     help='Access to give the user.  Must be one of the following values: '
#     + " ".join(scp_api.c_PERMISSIONS),
# )

## Create cluster file upload subparser
parser_upload_cluster = subargs.add_parser(
    c_TOOL_CLUSTER,
    help="Upload a cluster file. \""
    + args.prog
    + " "
    + c_TOOL_CLUSTER
    + " -h\" for more details",
)
parser_upload_cluster.add_argument(
    '--file', dest='cluster_file', required=True, help='Cluster file to load.'
)
parser_upload_cluster.add_argument(
    '--study-name',
    required=True,
    help='Name of the study to add the file.',
)
parser_upload_cluster.add_argument(
    '--description',
    default="Coordinates and optional metadata to visualize clusters.",
    help='Text describing the cluster file.',
)
parser_upload_cluster.add_argument(
    '--cluster-name',
    required=True,
    help='Name of the clustering that will be used to refer to the plot.',
)
parser_upload_cluster.add_argument(
    '--x', dest='x_label', default=None, help='X axis label (test).'
)
parser_upload_cluster.add_argument(
    '--y', dest='y_label', default=None, help='Y axis label (test).'
)
parser_upload_cluster.add_argument(
    '--z', dest='z_label', default=None, help='Z axis label (test).'
)

## Create expression file upload subparser
parser_upload_expression = subargs.add_parser(
    c_TOOL_EXPRESSION,
    help="Upload a gene expression matrix file. \""
    + args.prog
    + " "
    + c_TOOL_EXPRESSION
    + " -h\" for more details",
)
parser_upload_expression.add_argument(
    '--file', dest='expression_file', required=True, help='Expression file to load.'
)
parser_upload_expression.add_argument(
    '--study-name',
    required=True,
    help='Name of the study to add the file.',
)
parser_upload_expression.add_argument(
    '--description',
    default='Gene expression in cells',
    help='Text describing the gene expression matrix file.',
)
parser_upload_expression.add_argument(
    '--species',
    required=True,
    help='Species from which the data is generated.',
)
parser_upload_expression.add_argument(
    '--genome',
    required=True,
    help='Genome assembly used to generate the data.',
)
# TODO: Add upstream support for this in SCP RESI API
# parser_upload_expression.add_argument(
#     '--axis_label', dest='axis_label',
#     default='',
#     help=''
# )

## Create metadata file upload subparser
parser_upload_metadata = subargs.add_parser(
    c_TOOL_METADATA,
    help="Upload a metadata file. \""
    + args.prog
    + " "
    + c_TOOL_METADATA
    + " -h\" for more details",
)
parser_upload_metadata.add_argument(
    '--file', dest='metadata_file', required=True, help='Metadata file to load.'
)
parser_upload_metadata.add_argument(
    '--use-convention',
    help='Whether to use metadata convention: validates against standard vocabularies, and will enable faceted search on this data',
    action='store_true'
)
parser_upload_metadata.add_argument(
    '--validate-against-convention',
    help='Validates against standard vocabularies prior to upload',
    action='store_true'
)
parser_upload_metadata.add_argument(
    '--study-name',
    required=True,
    help='Name of the study to add the file.',
)
parser_upload_metadata.add_argument(
    '--description',
    default='',
    help='Text describing the metadata file.',
)

if __name__ == '__main__':
    parsed_args = args.parse_args()
    if parsed_args.verbose:
        print("Args----")
        print(vars(parsed_args))
        print("-----Args")

    verbose = parsed_args.verbose

    env_origin_map = {
        'development': 'https://localhost',
        'staging': 'https://single-cell-staging.broadinstitute.org',
        'production': 'https://singlecell.broadinstitute.org',
    }
    origin = env_origin_map[parsed_args.environment]
    api_base = origin + '/single_cell/api/v1/'

    # Login connection
    connection = login(
        manager=None, dry_run=parsed_args.dry_run, api_base=api_base, verbose=verbose
    )

    ## Handle list studies
    if hasattr(parsed_args, "summarize_list"):
        if verbose:
            print("START LIST STUDIES")
        ret = connection.get_studies(dry_run=parsed_args.dry_run)
        manage_call_return(ret)
        print(
            "You have access to "
            + str(len(ret[scp_api.c_STUDIES_RET_KEY]))
            + " studies."
        )
        if not parsed_args.summarize_list:
            print(os.linesep.join(ret[scp_api.c_STUDIES_RET_KEY]))

    ## Create new study
    if hasattr(parsed_args, "study_description") and not parsed_args.study_name is None:
        if verbose:
            print("START CREATE STUDY")
        is_public = not parsed_args.is_private
        ret = connection.create_study(
            study_name=parsed_args.study_name,
            study_description=parsed_args.study_description,
            branding=parsed_args.branding,
            billing=parsed_args.billing,
            is_public=is_public,
            dry_run=parsed_args.dry_run,
        )
        manage_call_return(ret)
        if succeeded(ret):
            print('Created study')

    ## Get a study attribute
    if parsed_args.command == c_TOOL_STUDY_GET_ATTR:
        if verbose:
            print("STARTING GET ATTRIBUTE")
        ret = connection.get_study_attribute(
            study_name=parsed_args.study_name,
            attribute=parsed_args.attribute,
            dry_run=parsed_args.dry_run,
        )
        manage_call_return(ret)
        print('Study {}:'.format(parsed_args.attribute))
        print(ret[scp_api.c_ATTR_RET_KEY])

    ## Edit a study description
    if parsed_args.command == c_TOOL_STUDY_EDIT_DESC:
        if verbose:
            print("STARTING EDIT DESCRIPTION")

        if parsed_args.from_file:
            with open(parsed_args.new_description, 'r') as d_file:
                new_description = d_file.read()
        else:
            new_description = parsed_args.new_description


        ret = connection.edit_study_description(
            study_name=parsed_args.study_name,
            new_description=new_description,
            accept_html=parsed_args.accept_html,
            dry_run=parsed_args.dry_run,
        )
        manage_call_return(ret)
        if succeeded(ret):
            print('Updated study description')

    ## Get all external resources from a study
    if parsed_args.command == c_TOOL_STUDY_GET_EXT:
        if verbose:
            print("STARTING GET EXTERNAL RESOURCES")
        ret = connection.get_study_external_resources(
            study_name=parsed_args.study_name,
            dry_run=parsed_args.dry_run,
        )
        manage_call_return(ret, verbose)
        print('Study external resources: \n')
        # Returns in dict format -- table format might be better
        print(ret[scp_api.c_EXT_RET_KEY])

    ## Delete all external resources from a study
    if parsed_args.command == c_TOOL_STUDY_DEL_EXT:
        if verbose:
            print("STARTING DELETE EXTERNAL RESOURCES")

        # first get all external resource ids
        ret = connection.get_study_external_resources(
            study_name=parsed_args.study_name,
            dry_run=parsed_args.dry_run,
        )
        manage_call_return(ret, verbose)
        ext_ids = [res['_id']['$oid'] for res in ret['external_resources']]
        if not ext_ids:
            print('No external resources associated with study.')
            exit()
        # confirm deletion with user
        confirmed = confirm("Delete {} external resources associated ".format(len(ext_ids)) +
                            "with study {}?".format(parsed_args.study_name))
        if confirmed:
            if verbose:
                print('Will continue deleting resources.')
            for ext_id in ext_ids:
                ret = connection.delete_study_external_resource(
                    study_name=parsed_args.study_name,
                    resource_id=ext_id,
                    dry_run=parsed_args.dry_run,
                )
                manage_call_return(ret, verbose)
            print('Deleted all external resources')

    ## Create new external resource for a study
    if parsed_args.command == c_TOOL_STUDY_CREATE_EXT:
        if verbose:
            print("STARTING CREATE EXTERNAL RESOURCE")
        ret = connection.create_study_external_resource(
            study_name=parsed_args.study_name,
            title=parsed_args.title,
            url=parsed_args.url,
            description=parsed_args.description,
            publication_url=parsed_args.publication_url,
            dry_run=parsed_args.dry_run,
        )
        manage_call_return(ret, verbose)
        if succeeded(ret):
            print('Created external resource')

    ## Share with user
    if hasattr(parsed_args, "permission"):
        if verbose:
            print("START SET PERMISSION")
        ret = connection.set_permission(
            study_name=parsed_args.study_name,
            email=parsed_args.email,
            access=parsed_args.permission,
            dry_run=parsed_args.dry_run,
        )
        manage_call_return(ret)
        if succeeded(ret):
            print('Set permission')

    ## Validate files
    if parsed_args.validate and not hasattr(parsed_args, "summarize_list"):

        if verbose:
            print("START VALIDATE FILES")

        if hasattr(parsed_args, "metadata_file") and parsed_args.use_convention:
            validate_metadata_file(parsed_args.metadata_file)

        # command = ["python3 verify_portal_file.py"]
        #
        # if hasattr(parsed_args, "cluster_file"):
        #     command.extend(["--coordinates-file", parsed_args.cluster_file])
        # if hasattr(parsed_args, "expression_file"):
        #     command.extend(["--expression-files", parsed_args.expression_file])
        # if hasattr(parsed_args, "metadata_file"):
        #     command.extend(["--metadata-file", parsed_args.metadata_file])
        #
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
        if verbose:
            print("START UPLOAD CLUSTER FILE")
        connection = login(manager=connection, dry_run=parsed_args.dry_run)
        ret = connection.upload_cluster(
            file=parsed_args.cluster_file,
            study_name=parsed_args.study_name,
            cluster_name=parsed_args.cluster_name,
            description=parsed_args.description,
            x=parsed_args.x_label,
            y=parsed_args.y_label,
            z=parsed_args.z_label,
            dry_run=parsed_args.dry_run,
        )
        manage_call_return(ret)
        if succeeded(ret):
            print('Uploaded and began parse of cluster file')

    ## Upload metadata file
    if hasattr(parsed_args, "metadata_file"):
        if verbose:
            print("START UPLOAD METADATA FILE")
        connection = login(manager=connection, dry_run=parsed_args.dry_run)
        print(f'connection is {connection}')
        ret = connection.upload_metadata(
            file=parsed_args.metadata_file,
            use_convention=parsed_args.use_convention,
            study_name=parsed_args.study_name,
            dry_run=parsed_args.dry_run,
        )
        manage_call_return(ret)
        if succeeded(ret):
            print('Uploaded and began parse of metadata file')

    ## Upload expression file
    if hasattr(parsed_args, "expression_file"):
        if verbose:
            print("START UPLOAD EXPRESSION FILE")
        connection = login(manager=connection, dry_run=parsed_args.dry_run)
        ret = connection.upload_expression_matrix(
            file=parsed_args.expression_file,
            study_name=parsed_args.study_name,
            species=parsed_args.species,
            genome=parsed_args.genome,
            dry_run=parsed_args.dry_run,
        )
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
