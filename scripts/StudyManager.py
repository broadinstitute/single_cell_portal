# -*- coding: utf-8 -*-

import requests

# Constants
c_AUTH = 'Authorization'
c_CODE_RET_KEY = "code"
c_STUDIES_RET_KEY = "studies"
c_SUCCESS_RET_KEY = "success"

## Standard Error Codes
c_STUDY_EXISTS = 101
c_STUDY_EXISTS_TEXT = "Can not create a study with a name that is in use."
c_NO_ERROR = 0
c_NO_ERROR_TEXT = "No error occurred."

# The expected header
class StudyManager:

    def __init__(self):
        print("INIT")
        self.api = "https://portals.broadinstitute.org/single_cell/api/v1/"
        self.studies = None

    def login(self, token):
        """
        :param token: User token to use with API
        :return: Boolean Indicator of success or failure (False)
        """
        print("LOGIN")
        self.token = token
        self.studies = None

    def do_get(self, command):
        print("DO GET")
        print(command)
        head = {c_AUTH:'token {}'.format(self.token),
                'Accept':'application/json'}
        r = requests.get(command, headers=head)
        if(r.status_code != 200):
            raise BaseException(str(r))
        return(r)

    def do_post(self, command, values):
        print("DO PUT")
        print(command)
        print(values)
        head = {c_AUTH:'token {}'.format(self.token),
                'Accept':'application/json'}
        r = requests.post(command, headers=head, json=values)
        if(r.status_code != 200):
            raise BaseException(str(r))
        return(r)

    def describe_error_code(error_code):
        ret_error_codes = {
            c_STUDY_EXISTS:c_STUDY_EXISTS_TEXT,
            c_NO_ERROR:c_NO_ERROR_TEXT
            }
        return(ret_error_codes.get(error_code, "That error code is not in use."))

    def get_studies(self):
        print("GET STUDIES")
        resp = self.do_get(self.api + "studies")
        self.studies = [str(element.get('name')) for element in resp.json()]
        return({
            c_SUCCESS_RET_KEY:True,
            c_CODE_RET_KEY:c_NO_ERROR,
            c_STUDIES_RET_KEY:self.studies
        })

    def create_study(self, studyName,
                     studyDescription="Single Cell Genomics study",
                     isPublic=False):
        print("CREATE STUDY:: " + studyName)
        if(self.studies is None):
            self.get_studies()
        if(studyName in self.studies):
            return ({
                c_SUCCESS_RET_KEY: False,
                c_CODE_RET_KEY: c_STUDY_EXISTS
            })
        studyData = {"name": studyName,
                     "description":studyDescription,
                     "public":isPublic}
        resp = self.do_post(command=self.api + "studies", values=studyData)
        self.studies.append(studyName)
        return({
            c_SUCCESS_RET_KEY:True,
            c_CODE_RET_KEY:c_NO_ERROR
        })

