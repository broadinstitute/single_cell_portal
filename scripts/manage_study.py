import argparse
import os
import StudyManager


def manageCallReturn(callReturn):
    # Print error code and describe code then exit if not sucess
    print("Error Code = " + str(callReturn[StudyManager.c_CODE_RET_KEY]))
    print(StudyManager.StudyManager.describe_error_code(callReturn[StudyManager.c_CODE_RET_KEY]))
    if(not callReturn[StudyManager.c_SUCCESS_RET_KEY]):
        exit(callReturn[StudyManager.c_CODE_RET_KEY])

args = argparse.ArgumentParser(
    prog='manage_study.py',
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter
)
args.add_argument(
    '--create_study', dest='createStudy', action='store_true',
    help='Create a new study.'
)
args.add_argument(
    '--list_studies', dest='listStudies', action='store_true',
    help='List the studies editable by this user.'
)
args.add_argument(
    '--study_description', dest='studyDescription',
    default="Single Cell Genomics Study",
    help='Short description of the study.'
)
args.add_argument(
    '--study_name', dest='studyName',
    help='The short name of the study.'
)
args.add_argument(
    '--token', dest='token', required=True,
    help='Personal token after logging into Google (Oauth2). This token is not persisted after the finish of the script'
)
parsed_args = args.parse_args()

manage = StudyManager.StudyManager()
manage.login(parsed_args.token)

## Handle list studies
if(parsed_args.listStudies):
    print("LIST STUDIES")
    ret = manage.get_studies()
    manageCallReturn(ret)
    print("There are "+str(len(ret[StudyManager.c_STUDIES_RET_KEY]))+" studies to which you have access.")
    print(os.linesep.join(ret[StudyManager.c_STUDIES_RET_KEY]))

## Create new study
if(parsed_args.createStudy):
    print("CREATE STUDY")
    ret = manage.create_study(studyName=parsed_args.studyName,
                              studyDescription=parsed_args.studyDescription)
    manageCallReturn(ret)

## Check files


## Upload coordinate file


## Upload metadata file


## Upload expression file