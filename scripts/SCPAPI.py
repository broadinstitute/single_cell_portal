# -*- coding: utf-8 -*-

import requests
import Commandline
import os

# Constants
c_AUTH = 'Authorization'
c_CODE_RET_KEY = "code"
c_RESPONSE = "response"
c_STUDIES_RET_KEY = "studies"
c_SUCCESS_RET_KEY = "success"

## Standard Error Codes
c_STUDY_EXISTS = 101
c_STUDY_EXISTS_TEXT = "Can not create a study with a name that is in use."
c_NO_ERROR = 0
c_NO_ERROR_TEXT = "No error occurred."

## API Error codes
c_API_OK = 200
c_API_AUTH = 401
c_API_AUTH_TEXT = "User is not authenticated"
c_API_AUTH_STUDY = 403
c_API_AUTH_STUDY_TEXT = "User is not authorized to edit study"
c_API_UNKNOWN_STUDY = 404
c_API_UNKNOWN_STUDY_TEXT = "Study is not found"
c_API_CONTENT_HEADERS = 406
c_API_CONTENT_HEADERS_TEXT = "Accept or Content-Type headers missing or misconfigured"
c_API_INVALID_STUDY = 422
c_API_INVALID_STUDY_TEXT = "Study validation failed"
c_API_BACKEND_ERROR = 500
c_API_BACKEND_ERROR_TEXT = "Server error when attempting to synchronize FireCloud workspace or access GCS objects"

# The expected header
class APIManager:

    def __init__(self):
        print("INIT")
        self.api = "https://portals.broadinstitute.org/single_cell/api/v1/"
        self.studies = None

    def login(self, token=None, test=False):
        """
        :param token: User token to use with API
        :return: Boolean Indicator of success or failure (False)
        """
        print("LOGIN")
        if token is None:
            token = APIManager.do_browser_login(test=test)
        self.token = token
        self.studies = None

    def do_browser_login(test=False):
        print("BROWSER LOGIN")
        if test:
            return("TESTING_TOKEN")
        cmdline = Commandline.Commandline()
        cmdline.func_CMD(command="gcloud auth application-default login")
        cmd_ret = cmdline.func_CMD(command="gcloud auth application-default print-access-token",stdout=True)
        return(cmd_ret.decode("ASCII").strip(os.linesep))

    def do_get(self, command, test=False):
        print("DO GET")
        print(command)
        if test:
            return({c_SUCCESS_RET_KEY: True,c_CODE_RET_KEY: c_API_OK})
        head = {c_AUTH:'token {}'.format(self.token),
                'Accept':'application/json'}
        return(APIManager.check_api_return(requests.get(command, headers=head)))

    def do_post(self, command, values, test=False):
        print("DO PUT")
        print(command)
        print(values)
        if test:
            return({c_SUCCESS_RET_KEY: True,c_CODE_RET_KEY: c_API_OK})
        head = {c_AUTH:'token {}'.format(self.token),
                'Accept':'application/json'}
        return(APIManager.check_api_return(requests.post(command, headers=head, json=values)))

    def describe_error_code(error_code):
        ret_error_codes = {
            c_STUDY_EXISTS:c_STUDY_EXISTS_TEXT,
            c_NO_ERROR:c_NO_ERROR_TEXT,
            c_API_OK:c_NO_ERROR_TEXT,
            c_API_AUTH:c_API_AUTH_TEXT,
            c_API_AUTH_STUDY:c_API_AUTH_STUDY_TEXT,
            c_API_UNKNOWN_STUDY:c_API_UNKNOWN_STUDY_TEXT,
            c_API_CONTENT_HEADERS:c_API_CONTENT_HEADERS_TEXT,
            c_API_INVALID_STUDY:c_API_INVALID_STUDY_TEXT,
            c_API_BACKEND_ERROR:c_API_BACKEND_ERROR_TEXT
        }
        return(ret_error_codes.get(error_code, "That error code is not in use."))

    def check_api_return(ret):
        api_return = {}
        api_return[c_SUCCESS_RET_KEY] = ret.status_code == c_API_OK
        api_return[c_CODE_RET_KEY] = ret.status_code
        api_return[c_RESPONSE] = ret
        return(api_return)

    def get_studies(self, test=False):
        print("GET STUDIES")
        resp = self.do_get(self.api + "studies",test=test)
        if test:
            resp[c_STUDIES_RET_KEY] = ["TESTING 1","TESTING 2"]
        else:
            if(resp[c_SUCCESS_RET_KEY]):
                self.studies = [str(element.get('name')) for element in resp[c_RESPONSE].json()]
                resp[c_STUDIES_RET_KEY] = self.studies
        return(resp)

    def create_study(self, studyName,
                     studyDescription="Single Cell Genomics study",
                     isPublic=False,
                     test=False):
        print("CREATE STUDY:: " + studyName)
        # If we don't know what studies they have get them so we do not create a study already existing.
        if self.studies is None:
            ret = self.get_studies()
            if not ret[c_SUCCESS_RET_KEY]:
                return(ret)
        if studyName in self.studies:
            return ({
                c_SUCCESS_RET_KEY: False,
                c_CODE_RET_KEY: c_STUDY_EXISTS
            })
        studyData = {"name": studyName,
                     "description":studyDescription,
                     "public":isPublic}
        resp = self.do_post(command=self.api + "studies", values=studyData, test=test)
        if resp[c_SUCCESS_RET_KEY]:
            self.studies.append(studyName)
        return(resp)

