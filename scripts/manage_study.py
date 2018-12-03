import argparse
import os
import SCPAPI


def manageCallReturn(callReturn):
    # Print error code and describe code then exit if not sucess
    print("Error Code = " + str(callReturn[SCPAPI.c_CODE_RET_KEY]))
    print(SCPAPI.APIManager.describe_error_code(callReturn[SCPAPI.c_CODE_RET_KEY]))
    if(not callReturn[SCPAPI.c_SUCCESS_RET_KEY]):
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
    '--token', dest='token', required=True,
    help='Personal token after logging into Google (Oauth2). This token is not persisted after the finish of the script'
)

# Create tools (sub parser)
subargs = args.add_subparsers()
parser_create_studies = subargs.add_parser("Create_Study",
    help="Used to create studies. \""+args.prog+" Create_Study -h\" for more details")
parser_create_studies.add_argument(
    '--create_study', dest='createStudy', action='store_true',
    help='Create a new study.'
)
parser_create_studies.add_argument(
    '--study_description', dest='studyDescription',
    default="Single Cell Genomics Study",
    help='Short description of the study.'
)
parser_create_studies.add_argument(
    '--study_name', dest='studyName',
    help='The short name of the study.'
)
parsed_args = args.parse_args()

manage = SCPAPI.APIManager()
manage.login(parsed_args.token)

## Handle list studies
if(parsed_args.listStudies):
    print("LIST STUDIES")
    ret = manage.get_studies()
    manageCallReturn(ret)
    print("There are "+str(len(ret[SCPAPI.c_STUDIES_RET_KEY]))+" studies to which you have access.")
    print(os.linesep.join(ret[SCPAPI.c_STUDIES_RET_KEY]))

## Create new study
if(parsed_args.createStudy):
    print("CREATE STUDY")
    ret = manage.create_study(studyName=parsed_args.studyName,
                              studyDescription=parsed_args.studyDescription)
    manageCallReturn(ret)

## Check files

## Validate and Upload coordinate file

## Validate and Upload metadata file

## Validate and Upload expression file

## Validate and Upload 10X files

## Validate and Upload 10X directory

## Validate and Upload fastqs

## Validate and Upload bams

