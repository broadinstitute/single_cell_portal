# -*- coding: utf-8 -*-

import requests
import Commandline
import random
import string
import os

# Constants
c_AUTH = 'Authorization'
c_BOUNDARY_LENGTH = 20
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
c_API_BACKEND_ERROR_TEXT = "Internal server error"

# Share access modes
c_ACCESS_EDIT = "Edit"
c_ACCESS_REVIEWER = "Reviewer"
c_ACCESS_VIEW = "View"
c_ACCESS_REMOVE = "Remove"
c_PERMISSIONS = [c_ACCESS_EDIT, c_ACCESS_REVIEWER, c_ACCESS_VIEW, c_ACCESS_REMOVE]

# SCP Portal Specific
c_CLUSTER_FILE_TYPE = "Cluster"
c_TEXT_TYPE = "text/plain"
c_INVALID_STUDYDESC_CHAR = ["<",".","+","?",">"]
c_VALID_STUDYNAME_CHAR = string.ascii_letters + string.digits + "".join([" ","-",".","/","(",")","+",",",":"])

# Matrix API specific
c_MATRIX_API_OK = 200
c_MATRIX_REQUEST_API_OK = 202
c_MATRIX_BAD_FORMAT = 102
c_MATRIX_BAD_FORMAT_TEXT = "The requested format is not supported in the service."


class APIManager:
    '''
    Base class for REST API interaction. Handles common operations.
    '''

    def login(self, token=None, test=False):
        """
        Authenticates as user and get's token to perform actions on the user's behalf.

        :param token: User token to use with API
        :param test: If true, will run in testing mode, running as a dry run with no actual execution of functionality.
        :return: Boolean Indicator of success or failure (False)
        """

        ## TODO add in auth from a file.
        print("LOGIN")
        if token is None:
            token = APIManager.do_browser_login(test=test)
        self.token = token
        self.studies = None

    def do_browser_login(test=False):
        '''
        Authenticate through the browser

        :param test: If true, will run in testing mode, running as a dry run with no actual execution of functionality.
        :return: Authentication token
        '''

        print("BROWSER LOGIN")
        if test:
            print("TESTING:: Did not login")
            return("TESTING_TOKEN")
        cmdline = Commandline.Commandline()
        cmdline.func_CMD(command="gcloud auth application-default login")
        cmd_ret = cmdline.func_CMD(command="gcloud auth application-default print-access-token",stdout=True)
        return(cmd_ret.decode("ASCII").strip(os.linesep))

    def do_get(self, command, test=False):
        '''
        Perform a GET.

        :param command: String GET command to send to the REST endpoint
        :param test: If true, will run in testing mode, running as a dry run with no actual execution of functionality.
        :return: Return dict with response and error codes/status
        '''

        ## TODO add timeout and exception handling (Timeout exeception)
        print("DO GET")
        print(command)
        if test:
            return({c_SUCCESS_RET_KEY: True,c_CODE_RET_KEY: c_API_OK})
        head = {'Accept': 'application/json'}
        if hasattr(self,"token"):
            head[c_AUTH] = 'token {}'.format(self.token)
        return(APIManager.check_api_return(requests.get(command, headers=head)))

    def do_post(self, command, values, files=None, test=False):
        '''
        *** In development ***
        Perform POST.

        :param command: String POST command to send to the REST endpoint.
        :param values: Parameter values to send {name: value}
        :param files:
        :param test: If true, will run in testing mode, running as a dry run with no actual execution of functionality.
        :return: Return dict with response and error codes/status
        '''

        ## TODO addtimeout and exception handling (Timeout exeception)
        print("DO PUT")
        print(command)
        print(values)
        print(files)
        if test:
            print("TESTING:: Returning success.")
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
        '''
        Perform PATCH

        :param command: String PATCH command to send to the REST endpoint
        :param values: Parameter values to send {name: value}
        :param test: If true, will run in testing mode, running as a dry run with no actual execution of functionality.
        :return: Return dict with response and error code/status
        '''

        ## TODO add timeout and exception handling (Timeout exeception)
        print("DO PATCH")
        print(command)
        print(values)
        if test:
            return({c_SUCCESS_RET_KEY: True,c_CODE_RET_KEY: c_API_OK})
        head = {c_AUTH: 'token {}'.format(self.token), 'Accept': 'application/json'}
        return(APIManager.check_api_return(requests.patch(command, headers=head, json=values)))

    def do_delete(self, command, test=False):
        '''
        Perform Delete

        :param command: String DELETE command to send to the REST endpoint
        :param test: If true, will run in testing mode, running as a dry run with no actual execution of functionality.
        :return: Return dict with response and error code/status
        '''

        ## TODO add timeout and exception handling (Timeout exeception)
        print("DO DELETE")
        print(command)
        if test:
            return({c_SUCCESS_RET_KEY: True,c_CODE_RET_KEY: c_DELETE_OK})
        head = {c_AUTH: 'token {}'.format(self.token), 'Accept': 'application/json'}
        return(APIManager.check_api_return(requests.delete(command, headers=head)))

    def check_api_return(ret):
        '''
        Create dict that has if status code was successful, status code,and response

        :param ret: Response
        :return: Dict of response, error code, and status.
        '''

        print(ret)
        api_return = {}
        api_return[c_SUCCESS_RET_KEY] = ret.status_code in [c_API_OK, c_DELETE_OK]
        api_return[c_CODE_RET_KEY] = ret.status_code
        api_return[c_RESPONSE] = ret
        return(api_return)

    def get_boundary():
        '''
        Creates a random string that is likely to not be in a MIME message. Used as a boundary between MIME parts.

        :return: String
        '''

        base = string.ascii_lowercase + string.digits
        return("".join([random.choice(base) for i in range(c_BOUNDARY_LENGTH)]))


# The expected header
class SCPAPIManager(APIManager):
    '''
    API manager for the Single Cell Portal Endpoint.
    '''

    def __init__(self):
        '''
        Initialize for the SCP endpoint.
        '''

        APIManager.__init__(self)
        print("INIT")
        self.api = "https://portals.broadinstitute.org/single_cell/api/v1/"
        self.studies = None
        self.name_to_id = None
        self.species_genomes = {"cat":["felis_catus_9.0","felis_catus_8.0","felis_catus-6.2"]}

    def describe_error_code(error_code):
        '''
        Translate the error code to the text errors as per their endpoint documentation.

        :param error_code: Numeric error code to translate
        :return: String error code text
        '''

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

    def check_species_genome(self, species, genome=None):
        '''
        The SCP only support certain species, this checks the submitted species to make sure it is supported.

        :param species: String species to confirm is supported.
        :param genome: String, if provided optionally checks genome version.
        :return: Boolean, false indicates not supported.
        '''

        print("CHECK SPECIES (GENOME)")
        if not species.lower() in self.species_genomes:
            print(species+" : this species is not registered with the portal please email the team to have it added.")
            return(False)
        return(genome in self.species_genomes[species])

    def get_studies(self, test=False):
        '''
        Get studies available to user.

        :param test: If true, will run in testing mode, running as a dry run with no actual execution of functionality.
        :return: Response
        '''

        print("GET STUDIES")
        resp = self.do_get(self.api + "studies",test=test)
        if test:
            print("TESTING:: Returned dummy names.")
            resp[c_STUDIES_RET_KEY] = ["TESTING 1","TESTING 2"]
        else:
            if(resp[c_SUCCESS_RET_KEY]):
                self.studies = [str(element['name']) for element in resp[c_RESPONSE].json()]
                self.name_to_id = [[str(element['name']), str(element['_id']['$oid'])] for element in resp[c_RESPONSE].json()]
                self.name_to_id = {key: value for (key,value) in self.name_to_id}
                resp[c_STUDIES_RET_KEY] = self.studies
        return(resp)

    def isValidStudyDescription(self,studyDescription):
        '''
        Confirms a study description does not contain characters that are not allowed.

        :param studyDescription: String description
        :return: Boolean indicator of validity, True is valid
        '''

        noError = True
        for letter in studyDescription:
            if letter in c_INVALID_STUDYDESC_CHAR:
                print("The following letter is not valid in a study description:'"+letter+"'")
                noError = False
        return noError

    def isValidStudyName(self, studyName):
        '''
        Confirms a study name does not contain characters that are not allowed.

        :param studyName: String study name
        :return: Boolean indicator oc validity, True is valid
        '''

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
        '''
        Create a study name using the REST API.
        Confirms the study does not exist before creating.
        Confirms name and description are valid.

        :param studyName: String study name
        :param studyDescription: String study description
        :param branding: String branding
        :param billing: String FireCloud Billing object
        :param isPublic: Boolean indicator if the sudy should be public (True)
        :param test: If true, will run in testing mode, running as a dry run with no actual execution of functionality.
        :return: Response
        '''
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
        '''
        Sets permission on a study.

        :param studyName: String study name to update permissions
        :param email: String email (user) to update permission
        :param access: String access level for permission
        :param deliver_email: Boolean, is the user interested in email notifications for study changes (True, receive emails)
        :param test: If true, will run in testing mode, running as a dry run with no actual execution of functionality
        :return: Dict with response and additional information including status and errors
        '''
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
        studyId = self.study_name_to_id(studyName, test=test)

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
        '''
        Indicates if the user has access to a study of the given name

        :param studyName: String study name
        :param test: If true, will run in testing mode, running as a dry run with no actual execution of functionality
        :return: Boolean, True indicates the study is known to the user and exists
        '''
        print("STUDY EXISTS?")
        if self.studies is None:
            ret = self.get_studies(test=test)
            if not ret[c_SUCCESS_RET_KEY]:
                return False
                #### TODO throw exception
        if test:
            return(True)
        return(studyName in self.studies)

    def study_name_to_id(self, name, test=False):
        '''
        Changes the a study name into the correct a portal id

        :param name: String study name
        :param test: If true, will run in testing mode, running as a dry run with no actual execution of functionality.
        :return: String portal id
        '''
        print("STUDY NAME TO ID")
        if test:
            print("TESTING:: returning a dummy id")
            return("1")
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
        '''
        *** In development, not complete.***
        :param file:
        :param studyName:
        :param clusterName:
        :param description:
        :param species:
        :param genome:
        :param x:
        :param y:
        :param z:
        :param test: If true, will run in testing mode, running as a dry run with no actual execution of functionality.
        :return:
        '''
        print("UPLOAD CLUSTER FILE")

        import logging
        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True

        # Error if the study does not exist
        if not self.study_exists(studyName=studyName, test=test) and not test:
            return {
                c_SUCCESS_RET_KEY: False,
                c_CODE_RET_KEY: c_STUDY_DOES_NOT_EXIST
            }
        # Convert study name to study id
        # python manage_study.py upload-cluster --file ../demo_data/coordinates_example.txt --study apitest --cluster_name test-cluster --species "Felis catus" --genome "Felis_catus_9.0"
        # sutdy id 5c0aaa5e328cee0a3b19c4a9
        studyId = self.study_name_to_id(studyName, test=test)
        fileInfo = {"study_file":{"file_type":"Cluster",
                    "species":"Felis catus",
                    "name":"cluster"}}
        files = {"study_file":{"file_type":"Cluster",
                               "species":"Felis catus",
                               "name":"cluster",
                               "upload":open(file,'rb')}}
        ret = self.do_post(command=self.api + "studies/" + str(studyId) + "/study_files",
                           values={},
                           files=files,
                           test=test)
        print("HHH")
        print(ret["response"].text)
        dir(ret["response"])
        print("HHH@")
        return(ret)
        '''
        import urllib
        boundary = APIManager.get_boundary()
        content_type = 'multipart/form-data; boundary=%s' %  boundary
        boundary = boundary.encode('utf-8')

        body = b'--'+boundary+b'\r\n'
        body += b'Content-Disposition: form-data; name="study_file[file_type]"\r\n'
        body += b'\r\n'
        body += b'Cluster'
        body += b'--'+boundary+b'\r\n'
        body += b'Content-Disposition: form-data; name="study_file[upload]"; filename="'+os.path.basename(file).encode('utf-8')+b'"\r\n'
        body += b'Content-Type: text/plain\r\n'
        #body += b'\r\n'
        #body += open(file,'rb').read() + b'\r\n'
        body += b'--'+boundary+b'--\r\n'

        curReq = urllib.request.Request(self.api + "studies/" + str(studyId) + "/study_files")
        curReq.add_header('User-agent','Single Cell Portal User Scripts (https://portals.broadinstitute.org/single_cell)')
        curReq.add_header('Content-Type', content_type)
        curReq.add_header('Authorization',self.token)
        curReq.add_header('Accept', 'application/json')
        curReq.add_header('Content-Length',len(body))

        curReq.data = body
        [print(i) for i in curReq.header_items()]
        print("BODY")
        print(curReq.data)
        ret = None
        try:
            ret = urllib.request.urlopen(curReq)
            print("-----")
            print(dir(ret))
            print(ret.getcode())
            print("-----")
            return(ret)
        except urllib.error.HTTPError as e:
            print(e.code)
            print(e.reason)
            print(e.headers)
            return(ret)

        #print("-----")
        #print(dir(ret[c_RESPONSE]))
        #print("-----")
        #print(ret[c_RESPONSE].json())
        #print(ret[c_RESPONSE].headers)
        #print("------url")
        #print(ret[c_RESPONSE].url)
        #print("-----url")
        #print(ret[c_RESPONSE].history)
        #print(ret[c_RESPONSE].content)
        #print(ret[c_RESPONSE].raw)
        '''


class DSSAPIManager(APIManager):
    '''
    API manager for the HCA DSS
    '''

    def __init__(self):
        '''
        Initialize for the DSS endpoint
        '''

        APIManager.__init__(self)
        print("INIT")
        self.api = "https://dss.data.humancellatlas.org/v1/"


class MatrixAPIManager(APIManager):
    '''
    API manager for Matrix service
    '''

    def __init__(self):
        '''
        Initialize for the expression matrix service
        '''

        APIManager.__init__(self)
        print("INIT MATRIX API")
        self.api = "https://matrix.data.humancellatlas.org/v0/matrix/"
        self.supportedTypes = None

    def describe_error_code(error_code):
        '''
        Translate the error code to the text errors as per their endpoint documentation.

        :param error_code: Numeric error code to translate
        :return: String error code text
        '''

        ret_error_codes = {
            c_MATRIX_API_OK:c_NO_ERROR_TEXT,
            c_MATRIX_REQUEST_API_OK:c_NO_ERROR_TEXT,
            c_MATRIX_BAD_FORMAT:c_MATRIX_BAD_FORMAT_TEXT,
            c_API_SYNTAX_ERROR:c_API_SYNTAX_ERROR_TEXT
        }
        return(ret_error_codes.get(error_code, "That error code is not in use."))

    def get_supported_types(self, test=False):
        '''
        Query and update supported file types for delivery by the matrix service

        :param test: If true, will run in testing mode, running as a dry run with no actual execution of functionality
        :return: Returns the response, also updates the supported types (in the Matrix Manager)
        '''
        print("GET SUPPORTED TYPES")
        if test:
            self.supportedTypes = ["test_type","test_type"]
            return {c_SUCCESS_RET_KEY: True}
        if self.supportedTypes is None:
            resp =self.do_get(self.api + "formats")
            if resp[c_SUCCESS_RET_KEY]:
                self.supportedTypes = resp[c_RESPONSE].json()
        return(resp)

    def request_matrix(self, ids, format="zarr", test=False):
        '''
        *** In development ****
        Request a matrix by supplying bundle IDs

        :param ids: HCA bundle ids
        :param format: String supported file format to format the matrix to be received
        :param test: If true, will run in testing mode, running as a dry run with no actual execution of functionality.
        :return: Response
        '''
        print("REQUEST MATRIX BY IDs")
        if not format in self.get_supported_types():
            return {c_SUCCESS_RET_KEY: False,
                    c_CODE_RET_KEY: c_MATRIX_BAD_FORMAT}
        bundleInfo = {"bundle_fqids":ids,"format":format}
        resp = self.do_post(self.api,
                            values=bundleInfo,
                            test=test)
        return(resp)

