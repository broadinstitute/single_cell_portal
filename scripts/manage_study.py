#! /usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import Commandline
import os
import SCPAPI

c_TOOL_STUDY = "create_study"
c_TOOL_CLUSTER = "upload_cluster"
c_TOOL_PERMISSION = "permission"

def manageCallReturn(callReturn):
    # Print error code and describe code then exit if not sucess
    print("Error Code = " + str(callReturn[SCPAPI.c_CODE_RET_KEY]))
    print(SCPAPI.APIManager.describe_error_code(callReturn[SCPAPI.c_CODE_RET_KEY]))
    if not callReturn[SCPAPI.c_SUCCESS_RET_KEY]:
        exit(callReturn[SCPAPI.c_CODE_RET_KEY])

#def get_token_browser():
#    "gcloud auth application-default login"
#   "gcloud auth application-default print-access-token"

args = argparse.ArgumentParser(
    prog='manage_study.py',
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter
)
args.add_argument(
    '--list_studies', dest='listStudies', action='store_true',
    help='List the studies editable by this user.'
)
args.add_argument(
    '--token', dest='token', default=None,
    help='Personal token after logging into Google (Oauth2). This token is not persisted after the finish of the script'
)
args.add_argument(
    '--test', dest='testing', action='store_true',
    help='This will turn on testing mode which will walk through and log what will occur without performing the actions.'
)

# Create tools (sub parser)
## Create study subparser
subargs = args.add_subparsers()
parser_create_studies = subargs.add_parser(c_TOOL_STUDY,
    help="Used to create studies. \""+args.prog+" "+c_TOOL_STUDY+" -h\" for more details")
parser_create_studies.add_argument(
    '--description', dest='studyDescription',
    default="Single Cell Genomics Study",
    help='Short description of the study.'
)
parser_create_studies.add_argument(
    '--study_name', dest='studyName', required=True,
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
    help="Used to change user permissions to studies. \""+args.prog+" "+c_TOOL_PERMISSION+" -h\" for more details")
parser_permissions.add_argument(
    '--email', dest='email', required=True,
    default='Single Cell Genomics Study',
    help='User email to update study permission.'
)
parser_permissions.add_argument(
    '--study_name', dest='studyName', required=True,
    help='The short name of the study.'
)
parser_permissions.add_argument(
    '--access', dest='permission', choices=SCPAPI.c_PERMISSIONS, required=True,
    help='The access to give the user. This can only be one of the following value:'+" ".join(SCPAPI.c_PERMISSIONS)
)

## Create cluster file upload subparser
parser_upload_cluster = subargs.add_parser(c_TOOL_CLUSTER,
    help="Used to upload cluster files. \""+args.prog+" "+c_TOOL_CLUSTER+" -h\" for more details")
parser_upload_cluster.add_argument(
    '--file', dest='clusterFile', required=True,
    help='Cluster file to load.'
)
parser_upload_cluster.add_argument(
    '--study_name', dest='studyName', required=True,
    help='The name of the study to add the file.'
)
parser_upload_cluster.add_argument(
    '--cluster_name', dest='clusterName', required=True,
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
    '--description', dest='clusterDescription',
    default="Coordinates and optional metadata to visualize clusters.",
    help='Text describing the cluster file.'
)
parser_upload_cluster.add_argument(
    '--x', dest='xLab',
    default=None,
    help='X axis label test.'
)
parser_upload_cluster.add_argument(
    '--y', dest='yLab',
    default=None,
    help='y axis label test.'
)
parser_upload_cluster.add_argument(
    '--z', dest='zLab',
    default=None,
    help='z axis label test.'
)
parser_upload_cluster.add_argument(
    '--no_validate', dest='validate',
    action='store_false',
    help='Check file locally before uploading.'
)


## TODO if no arguments are passed it logs in, stop logining in unless needed.
parsed_args = args.parse_args()
manage = SCPAPI.APIManager()
manage.login(token=parsed_args.token,
             test=parsed_args.testing)
print(vars(parsed_args))
## Handle list studies
if parsed_args.listStudies:
    print("LIST STUDIES")
    ret = manage.get_studies(test=parsed_args.testing)
    manageCallReturn(ret)
    print("There are "+str(len(ret[SCPAPI.c_STUDIES_RET_KEY]))+" studies to which you have access.")
    print(os.linesep.join(ret[SCPAPI.c_STUDIES_RET_KEY]))

## Create new study
if hasattr(parsed_args,"studyDescription") and not parsed_args.studyName is None:
    print("CREATE STUDY")
    ret = manage.create_study(studyName=parsed_args.studyName,
                              studyDescription=parsed_args.studyDescription,
                              branding=parsed_args.branding,
                              billing=parsed_args.billing,
                              test=parsed_args.testing)
    manageCallReturn(ret)

## Share with user
if hasattr(parsed_args,"permission"):
    print("SET PERMISSION")
    ret = manage.set_permission(studyName=parsed_args.studyName,
                                email=parsed_args.email,
                                access=parsed_args.permission,
                                test=parsed_args.testing)
    manageCallReturn(ret)

## Validate files
if hasattr(parsed_args,"clusterFile") and parsed_args.validate:
    print("VALIDATE CLUSTER FILE")
    if not parsed_args.testing:
        valid_code = Commandline.Commandline().func_CMD(" ".join(["verify_portal_file.py",
                                                                  "--coordinates_file",
                                                                  parsed_args.clusterFile]))
        print(valid_code)
        if not valid_code:
            print("There was an error validating the files, did not upload.")
            exit(valid_code)

## Validate and upload cluster file
if hasattr(parsed_args,"clusterFile"):
    print("UPLOAD CLUSTER FILE")
    ret = manage.upload_cluster(file=parsed_args.clusterFile,
                                studyName=parsed_args.studyName,
                                clusterName=parsed_args.clusterName,
                                description=parsed_args.clusterDescription,
                                species=parsed_args.species,
                                genome=parsed_args.genome,
                                x=parsed_args.xLab,
                                y=parsed_args.yLab,
                                z=parsed_args.zLab,
                                test=parsed_args.testing)
    manageCallReturn(ret)

## Upload metadata file

## Upload expression file
##--

## Validate and Upload and Sort 10X files

## Validate and Upload 10X directory

## Validate and Upload fastqs

## Validate and Upload bams

