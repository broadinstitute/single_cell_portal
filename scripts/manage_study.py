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
# List studies in SCP
$ python manage_study.py list-studies

# Get number of studies in SCP, using token to bypass browser log-in
$ python manage_study.py --token=`gcloud auth print-access-token` list-studies --summary

# Get help for list-studies subparser
$ python manage_study.py list-studies --help

"""

import argparse
import Commandline
import os
import SCPAPI

# Subparser tool names
c_TOOL_LIST_STUDY = "list-studies"
c_TOOL_CLUSTER = "upload-cluster"
c_TOOL_EXPRESSION = "upload-expression"
c_TOOL_METADATA = "upload-metadata"
c_TOOL_PERMISSION = "permission"
c_TOOL_STUDY = "create-study"

def manage_call_return(call_return):
    '''
    Accesses the error codes in the underlying library and check the return code.

    :param call_return: Dict returned from SCPAPI call with REST call return info
    :return: No return will exit on error
    '''
    # Print error code and describe code then exit if not sucess
    print("Error Code = " + str(call_return[SCPAPI.c_CODE_RET_KEY]))
    print(SCPAPI.SCPAPIManager.describe_error_code(call_return[SCPAPI.c_CODE_RET_KEY]))
    if not call_return[SCPAPI.c_SUCCESS_RET_KEY]:
        exit(call_return[SCPAPI.c_CODE_RET_KEY])

def login(manager=None,test=False):
    '''
    Login to authorize credentials.

    :param manager: API Manager
    :param test: If true, will run in testing mode, running as a dry run with no actual execution of functionality.
    :return:
    '''
    if manager is None:
        manager=SCPAPI.SCPAPIManager()
        manager.login(token=parsed_args.token,
                      test=test)
    return(manager)


args = argparse.ArgumentParser(
    prog='manage_study.py',
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter
)
args.add_argument(
    '--token', dest='token', default=None,
    help='Personal token after logging into Google (Oauth2). This token is not persisted after the finish of the script'
)
args.add_argument(
    '--test', dest='testing', action='store_true',
    help='Turn on testing mode which will walk through and log what will occur without performing the actions.'
)
args.add_argument(
    '--no-validate', dest='validate',
    action='store_false',
    help='Do not check file locally before uploading.'
)

# Create tools (subparser)
subargs = args.add_subparsers()

## List studies subparser
parser_list_studies = subargs.add_parser(c_TOOL_LIST_STUDY,
    help="List studies. \""+args.prog+" "+c_TOOL_LIST_STUDY+" -h\" for more details")
parser_list_studies.add_argument(
    '--summary', dest='summarize_list', action='store_true',
    help='Do not list but summarize only.'
)

## Create study subparser
parser_create_studies = subargs.add_parser(c_TOOL_STUDY,
    help="Create a study. \""+args.prog+" "+c_TOOL_STUDY+" -h\" for more details")
parser_create_studies.add_argument(
    '--description', dest='study_description',
    default="Single Cell Genomics Study",
    help='Short description of the study.'
)
parser_create_studies.add_argument(
    '--study-name', dest='study_name', required=True,
    help='The short name of the study.'
)
parser_create_studies.add_argument(
    '--branding', dest='branding', default=None,
    help='The portal branding to associate with the study.'
)
parser_create_studies.add_argument(
    '--billing', dest='billing', default=None,
    help='Portal billing project to associate with the study.'
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
    help='The short name of the study.'
)
parser_permissions.add_argument(
    '--access', dest='permission', choices=SCPAPI.c_PERMISSIONS, required=True,
    help='The access to give the user. This can only be one of the following value:'+" ".join(SCPAPI.c_PERMISSIONS)
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
    help='The name of the study to add the file.'
)
parser_upload_cluster.add_argument(
    '--cluster-name', dest='cluster_name', required=True,
    help='The name of the clustering that will be used to refer to the plot.'
)
parser_upload_cluster.add_argument(
    '--species', dest='species', required=True,
    help='The species from which the data is generated.'
)
parser_upload_cluster.add_argument(
    '--genome', dest='genome', required=True,
    help='Genome assembly used to generate the data.'
)
parser_upload_cluster.add_argument(
    '--description', dest='cluster_description',
    default="Coordinates and optional metadata to visualize clusters.",
    help='Text describing the cluster file.'
)
parser_upload_cluster.add_argument(
    '--x', dest='x_lab',
    default=None,
    help='X axis label test.'
)
parser_upload_cluster.add_argument(
    '--y', dest='y_lab',
    default=None,
    help='y axis label test.'
)
parser_upload_cluster.add_argument(
    '--z', dest='z_lab',
    default=None,
    help='z axis label test.'
)

## Create expression file upload subparser
parser_upload_expression = subargs.add_parser(c_TOOL_EXPRESSION,
    help="Upload a gene expression matrix file. \""+args.prog+" "+c_TOOL_EXPRESSION+" -h\" for more details")
parser_upload_expression.add_argument(
    '--file', dest='expression_file', required=True,
    help='Expression file to load.'
)

## Create metadata file upload subparser
parser_upload_metadata = subargs.add_parser(c_TOOL_METADATA,
    help="Upload a metadata file. \""+args.prog+" "+c_TOOL_METADATA+" -h\" for more details")
parser_upload_metadata.add_argument(
    '--file', dest='metadata_file', required=True,
    help='Metadata file to load.'
)

parsed_args = args.parse_args()
print("Args----")
print(vars(parsed_args))
print("-----Args")

# Login connection
connection = None

## Handle list studies
if hasattr(parsed_args, "summarize_list"):
    print("LIST STUDIES")
    connection = login(manager=connection, test=parsed_args.testing)
    ret = connection.get_studies(test=parsed_args.testing)
    manage_call_return(ret)
    print("You have access to "+str(len(ret[SCPAPI.c_STUDIES_RET_KEY]))+" studies.")
    if not parsed_args.summarize_list:
        print(os.linesep.join(ret[SCPAPI.c_STUDIES_RET_KEY]))

## Create new study
if hasattr(parsed_args, "study_description") and not parsed_args.study_name is None:
    print("CREATE STUDY")
    connection = login(manager=connection, test=parsed_args.testing)
    ret = connection.create_study(study_name=parsed_args.study_name,
                                  study_description=parsed_args.study_description,
                                  branding=parsed_args.branding,
                                  billing=parsed_args.billing,
                                  test=parsed_args.testing)
    manage_call_return(ret)

## Share with user
if hasattr(parsed_args, "permission"):
    print("SET PERMISSION")
    connection = login(manager=connection, test=parsed_args.testing)
    ret = connection.set_permission(study_name=parsed_args.study_name,
                                    email=parsed_args.email,
                                    access=parsed_args.permission,
                                    test=parsed_args.testing)
    manage_call_return(ret)

## Validate files
if parsed_args.validate and not hasattr(parsed_args, "summarize_list"):
    print("VALIDATE FILES")
    command = ["verify_portal_file.py"]

    if hasattr(parsed_args, "cluster_file"):
        command.extend(["--coordinates-file", parsed_args.cluster_file])
    if hasattr(parsed_args, "expression_file"):
        command.extend(["--expression-files", parsed_args.expression_file])
    if hasattr(parsed_args, "metadata_file"):
        command.extend(["--metadata-file", parsed_args.metadata_file])

    if parsed_args.testing:
        print("TESTING:: no command executed."+os.linesep+"Would have executed:"+os.linesep+" ".join(command))
    else:
        valid_code = Commandline.Commandline().func_CMD(" ".join(command))
        print(valid_code)
        if not valid_code:
            print("There was an error validating the files, did not upload. Code="+str(valid_code))
            exit(valid_code)

## Upload cluster file
if hasattr(parsed_args, "cluster_file"):
    print("UPLOAD CLUSTER FILE")
    connection = login(manager=connection, test=parsed_args.testing)
    ret = connection.upload_cluster(file=parsed_args.cluster_file,
                                    study_name=parsed_args.study_name,
                                    cluster_name=parsed_args.cluster_name,
                                    description=parsed_args.cluster_description,
                                    species=parsed_args.species,
                                    genome=parsed_args.genome,
                                    x=parsed_args.x_lab,
                                    y=parsed_args.y_lab,
                                    z=parsed_args.z_lab,
                                    test=parsed_args.testing)
    manage_call_return(ret)

## Upload metadata file
### TODO

## Upload expression file
### TODO

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

