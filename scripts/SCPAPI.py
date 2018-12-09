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
c_STUDY_DOES_NOT_EXIST = 102
c_STUDY_DOES_NOT_EXIST_TEXT = "The study does not exist, please create first."
c_INVALID_STUDY_NAME = 103
c_INVALID_STUDY_NAME_TEXT = "Invalid study name. Use alphanumeric, spaces, dashes, '.', '/', '(', ')', '+', ',', ':'"
c_INVALID_SHARE_MODE = 104
c_INVALID_SHARE_MODE_TEXT = "The access you want to give the user is not an access I understand. Please check."
c_INVALID_SHARE_MISSING = 105
c_INVALID_SHARE_MISSING_TEXT = "Can not remove the share, it does not exist."
c_NO_ERROR = 0
c_NO_ERROR_TEXT = "No error occurred."

## API Error codes
c_API_OK = 200
c_DELETE_OK = 204
c_API_SYNTAX_ERROR = 400
c_API_SYNTAX_ERROR_TEXT = "The request was malformed and has bad syntax."
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

# Share access modes
c_ACCESS_EDIT = "Edit"
c_ACCESS_REVIEWER = "Reviewer"
c_ACCESS_VIEW = "View"
c_ACCESS_REMOVE = "Remove"
c_PERMISSIONS = [c_ACCESS_EDIT, c_ACCESS_REVIEWER, c_ACCESS_VIEW, c_ACCESS_REMOVE]

# SCP Portal
c_CLUSTER_FILE_TYPE = "Cluster"
c_TEXT_TYPE = "text/plain"
c_INVALID_STUDYDESC_CHAR = ["<",".","+","?",">"]
c_VALID_STUDYNAME_CHAR = string.ascii_letters + string.digits + [" ","-",".","/","(",")","+",",",":"]

# The expected header
class APIManager:

    def __init__(self):
        print("INIT")
        self.api = "https://portals.broadinstitute.org/single_cell/api/v1/"
        self.studies = None
        self.name_to_id = None
        self.species_genomes = {"cat":["felis_catus_9.0","felis_catus_8.0","felis_catus-6.2"]}

    def login(self, token=None, test=False):
        """
        :param token: User token to use with API
        :return: Boolean Indicator of success or failure (False)
        """
        ## TODO add in auth from a file.
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
        ## TODO addtimeout and exception handling (Timeout exeception)
        print("DO GET")
        print(command)
        if test:
            return({c_SUCCESS_RET_KEY: True,c_CODE_RET_KEY: c_API_OK})
        head = {c_AUTH:'token {}'.format(self.token), 'Accept':'application/json'}
        return(APIManager.check_api_return(requests.get(command, headers=head)))

    def do_post(self, command, values, files=None, test=False):
        ## TODO addtimeout and exception handling (Timeout exeception)
        print("DO PUT")
        print(command)
        print(values)
        print(files)
        if test:
            return({c_SUCCESS_RET_KEY: True,c_CODE_RET_KEY: c_API_OK})
        head = {c_AUTH: 'token {}'.format(self.token),
                'Accept': 'application/json'}
        print(head)
        if files is None:
            return(APIManager.check_api_return(requests.post(command,
                                                             headers=head,
                                                             json=values)))
        else:
            return(APIManager.check_api_return(requests.post(command,
                                                             headers=head,
                                                             files=files,
                                                             json=values)))

    def do_patch(self, command, values, test=False):
        ## TODO addtimeout and exception handling (Timeout exeception)
        print("DO PATCH")
        print(command)
        print(values)
        if test:
            return({c_SUCCESS_RET_KEY: True,c_CODE_RET_KEY: c_API_OK})
        head = {c_AUTH: 'token {}'.format(self.token), 'Accept': 'application/json'}
        return(APIManager.check_api_return(requests.patch(command, headers=head, json=values)))

    def do_delete(self, command, test=False):
        ## TODO addtimeout and exception handling (Timeout exeception)
        print("DO DELETE")
        print(command)
        if test:
            return({c_SUCCESS_RET_KEY: True,c_CODE_RET_KEY: c_DELETE_OK})
        head = {c_AUTH: 'token {}'.format(self.token), 'Accept': 'application/json'}
        return(APIManager.check_api_return(requests.delete(command, headers=head)))

    def describe_error_code(error_code):
        ret_error_codes = {
            c_STUDY_EXISTS:c_STUDY_EXISTS_TEXT,
            c_STUDY_DOES_NOT_EXIST:c_STUDY_DOES_NOT_EXIST_TEXT,
            c_INVALID_STUDY_NAME:c_INVALID_STUDY_NAME_TEXT,
            c_INVALID_SHARE_MODE:c_INVALID_SHARE_MODE_TEXT,
            c_INVALID_SHARE_MISSING:c_INVALID_SHARE_MISSING_TEXT,
            c_NO_ERROR:c_NO_ERROR_TEXT,
            c_API_OK:c_NO_ERROR_TEXT,
            c_DELETE_OK:c_NO_ERROR_TEXT,
            c_API_AUTH:c_API_AUTH_TEXT,
            c_API_SYNTAX_ERROR:c_API_SYNTAX_ERROR_TEXT,
            c_API_AUTH_STUDY:c_API_AUTH_STUDY_TEXT,
            c_API_UNKNOWN_STUDY:c_API_UNKNOWN_STUDY_TEXT,
            c_API_CONTENT_HEADERS:c_API_CONTENT_HEADERS_TEXT,
            c_API_INVALID_STUDY:c_API_INVALID_STUDY_TEXT,
            c_API_BACKEND_ERROR:c_API_BACKEND_ERROR_TEXT
        }
        return(ret_error_codes.get(error_code, "That error code is not in use."))

    def check_api_return(ret):
        print(ret.url)
        api_return = {}
        api_return[c_SUCCESS_RET_KEY] = ret.status_code in [c_API_OK, c_DELETE_OK]
        api_return[c_CODE_RET_KEY] = ret.status_code
        api_return[c_RESPONSE] = ret
        return(api_return)

    def check_species_genome(self, species, genome=None):
        print("CHECK SPECIES (GENOME)")
        if not species.lower() in self.species_genomes:
            print(species+" : this species is not registered with the portal please email the team to have it added.")
            return(False)
        return(genome in self.species_genomes[species])

    def get_studies(self, test=False):
        print("GET STUDIES")
        resp = self.do_get(self.api + "studies",test=test)
        if test:
            resp[c_STUDIES_RET_KEY] = ["TESTING 1","TESTING 2"]
        else:
            if(resp[c_SUCCESS_RET_KEY]):
                self.studies = [str(element['name']) for element in resp[c_RESPONSE].json()]
                self.name_to_id = [[str(element['name']), str(element['_id']['$oid'])] for element in resp[c_RESPONSE].json()]
                self.name_to_id = {key: value for (key,value) in self.name_to_id}
                resp[c_STUDIES_RET_KEY] = self.studies
        return(resp)

    def isValidStudyDescription(self,studyDescription):
        noError = True
        for letter in studyDescription:
            if letter in c_INVALID_STUDYDESC_CHAR:
                print("The following letter is not valid in a study description:'"+letter+"'")
                noError = False
        return noError

    def isValidStudyName(self, studyName):
        noError = True
        for letter in studyName:
            if not letter in c_VALID_STUDYNAME_CHAR:
                print("The following letter is not valid in a study name:'"+letter+"'")
                noError = False
        return noError

    def create_study(self, studyName,
                     studyDescription="Single Cell Genomics study",
                     branding=None,
                     billing=None,
                     isPublic=False,
                     test=False):
        print("CREATE STUDY:: " + studyName)
        # Study variable validation
        ## Study must not exist
        if self.study_exists(studyName=studyName, test=test):
            return ({
                c_SUCCESS_RET_KEY: False,
                c_CODE_RET_KEY: c_STUDY_EXISTS
            })
        # Study name is restricted on letters
        if not isValidStudyName(studyName):
            return ({
                c_SUCCESS_RET_KEY: False,
                c_CODE_RET_KEY: c_INVALID_STUDY_NAME
            })
        # Study description should not have html and scripting
        if not isValidStudyDescription(studyDescription):
            return ({
                c_SUCCESS_RET_KEY: False,
                c_CODE_RET_KEY: c_INVALID_STUDY_DESC
            })

        # Make payload and do post
        studyData = {"name": studyName,
                     "description":studyDescription,
                     "public":isPublic}
        if not branding is None:
            studyData["firecloud_project"]=billing
        if not branding is None:
            studyData["branding_group_id"] = branding
        resp = self.do_post(command=self.api + "studies", values=studyData, test=test)
        # Update study list
        if resp[c_SUCCESS_RET_KEY] and not test:
            self.get_studies()
        return(resp)

    def set_permission(self, studyName, email, access, deliver_email=False, test=False):
        print("SET PERMISSION: "+" ".join(str(i) for i in [studyName, email, access]))
        # Make sure the access value is valid
        if not access in c_PERMISSIONS:
            return {
                c_SUCCESS_RET_KEY: False,
                c_CODE_RET_KEY: c_INVALID_SHARE_MODE
            }
        # Error if the study does not exist
        if not self.study_exists(studyName=studyName, test=test) and not test:
            return {
                c_SUCCESS_RET_KEY: False,
                c_CODE_RET_KEY: c_STUDY_DOES_NOT_EXIST
            }
        # Convert study name to study id
        studyId = self.study_name_to_id(studyName)

        # Get the share id for the email
        ret_shares = self.do_get(command=self.api + "studies/"+str(studyId)+"/study_shares",
                                 test=test)
        share_id = None
        for share in ret_shares[c_RESPONSE].json():
            if share["email"]==email:
                share_id = share['_id']['$oid']

        permissions_info = {"study_id": studyId,
                            "study_share":{"email":email,
                                           "permission":access,
                                           "deliver_emails":deliver_email}}
        if share_id is None:
            # Delete share
            if(access==c_ACCESS_REMOVE):
                return {
                    c_SUCCESS_RET_KEY: False,
                    c_CODE_RET_KEY: c_STUDY_DOES_NOT_EXIST
                }
            # Set shares for study given it does not exist
            ret = self.do_post(command=self.api+"studies/"+str(studyId)+"/study_shares",
                               values=permissions_info,
                               test=test)
            return(ret)
        else:
            # Delete share
            if(access==c_ACCESS_REMOVE):
                ret_delete = self.do_delete(command=self.api+"studies/"+str(studyId)+"/study_shares/"+share_id,
                                            test=test)
                return(ret_delete)
            # Update shares for a study that has the shares
            update_ret = self.do_patch(command=self.api+"studies/"+str(studyId)+"/study_shares/"+share_id,
                                       values=permissions_info,
                                       test=test)
            return(update_ret)

    def study_exists(self, studyName, test=False):
        print("STUDY EXISTS?")
        if self.studies is None:
            ret = self.get_studies()
            if not ret[c_SUCCESS_RET_KEY]:
                return False
                #### TODO throw exception
        if test:
            return(True)
        return(studyName in self.studies)

    def study_name_to_id(self, name, test=False):
        print("STUDY NAME TO ID")
        if test:
            return("ID 1")
        else:
            return(self.name_to_id.get(name, None))

    def upload_cluster(self, file,
                             studyName,
                             clusterName,
                             description="Cluster file.",
                             species=None,
                             genome=None,
                             x="X",
                             y="Y",
                             z="Z",
                             test=False):
        print("UPLOAD CLUSTER FILE")
        # Error if the study does not exist
        if not self.study_exists(studyName=studyName, test=test) and not test:
            return {
                c_SUCCESS_RET_KEY: False,
                c_CODE_RET_KEY: c_STUDY_DOES_NOT_EXIST
            }
        # Convert study name to study id
        studyId = self.study_name_to_id(studyName)
        fileInfo = {"study_id":studyId,
         #           "description":description,
         #           "name": clusterName,
          #          'Content-Type': 'multipart/form-data',
                    }
        files ={"file":open(file,'rb')}
              #                "species":species,
               #               "assembly":genome,

           #     "upload_file_name":os.path.basename(file),
          #      "upload_content_type":c_TEXT_TYPE}
        ret = self.do_post(command=self.api + "studies/" + str(studyId) + "/study_files",
                           values=fileInfo,
                           files=files,
                           test=test)
        print(ret)
        return(ret)