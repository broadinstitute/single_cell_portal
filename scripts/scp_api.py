# -*- coding: utf-8 -*-

"""Python library for interacting with SCP REST API

This library is used in client code like manage_study.py.  You can find
documentation on the upstream REST API that this module wraps at:
https://singlecell.broadinstitute.org/single_cell/api/swagger_docs/v1
"""

import requests
import urllib3
import random
import string
import os
import json

import logging

try:
    # Used when importing internally and in tests
    import Commandline
except ImportError:
    # Used when importing as external package
    from . import Commandline

# Constants
c_AUTH = 'Authorization'
c_BOUNDARY_LENGTH = 20
c_CODE_RET_KEY = "code"
c_RESPONSE = "response"
c_STUDIES_RET_KEY = "studies"
c_SUCCESS_RET_KEY = "success"
c_ATTR_RET_KEY = 'study_attribute'
c_EXT_RET_KEY = 'external_resources'

## Standard status codes
c_STUDY_EXISTS = 101
c_STUDY_EXISTS_TEXT = "Can not create a study with a name that is in use."
c_STUDY_DOES_NOT_EXIST = 102
c_STUDY_DOES_NOT_EXIST_TEXT = "The study does not exist, please create first."
c_INVALID_STUDY_NAME = 103
c_INVALID_STUDY_NAME_TEXT = "Invalid study name. Use alphanumeric, spaces, dashes, '.', '/', '(', ')', '+', ',', ':'"
c_INVALID_SHARE_MODE = 104
c_INVALID_SHARE_MODE_TEXT = (
    "The access you want to give the user is not an access I understand. Please check."
)
c_INVALID_SHARE_MISSING = 105
c_INVALID_SHARE_MISSING_TEXT = "Can not remove the share, it does not exist."
c_INVALID_STUDY_DESC = 106
c_INVALID_STUDY_DESC_TEXT = "Invalid characters used in study description."
c_ATTRIBUTE_DOES_NOT_EXIST = 107
c_ATTRIBUTE_DOES_NOT_EXIST_TEXT = "Requested study attribute does not exist."
c_NO_ERROR = 0
c_NO_ERROR_TEXT = "No error occurred."

## API status codes
c_API_OK = 200
c_DELETE_OK = 204
c_API_SYNTAX_ERROR = 400
c_API_SYNTAX_ERROR_TEXT = "The request was malformed and has bad syntax."
c_API_AUTH = 401
c_API_AUTH_TEXT = "User is not authenticated."
c_API_AUTH_STUDY = 403
c_API_AUTH_STUDY_TEXT = "User is not authorized to edit study."
c_API_UNKNOWN_STUDY = 404
c_API_UNKNOWN_STUDY_TEXT = "Study is not found"
c_API_CONTENT_HEADERS = 406
c_API_CONTENT_HEADERS_TEXT = "Accept or Content-Type headers missing or misconfigured."
c_API_INVALID_STUDY = 422
c_API_INVALID_STUDY_TEXT = "Study validation failed."
c_API_BACKEND_ERROR = 500
c_API_BACKEND_ERROR_TEXT = "Internal server error."

# Share access modes
c_ACCESS_EDIT = "Edit"
c_ACCESS_REVIEWER = "Reviewer"
c_ACCESS_VIEW = "View"
c_ACCESS_REMOVE = "Remove"
c_PERMISSIONS = [c_ACCESS_EDIT, c_ACCESS_REVIEWER, c_ACCESS_VIEW, c_ACCESS_REMOVE]

# SCP specific
c_CLUSTER_FILE_TYPE = "Cluster"
c_TEXT_TYPE = "text/plain"
c_INVALID_STUDYDESC_CHAR = ["<", ".", "+", "?", ">"]
c_VALID_STUDYNAME_CHAR = (
    string.ascii_letters
    + string.digits
    + "".join([" ", "-", ".", "/", "(", ")", "+", ",", ":"])
)

# Matrix API specific
c_MATRIX_API_OK = 200
c_MATRIX_REQUEST_API_OK = 202
c_MATRIX_BAD_FORMAT = 102
c_MATRIX_BAD_FORMAT_TEXT = "The requested format is not supported in the service."

cmdline = Commandline.Commandline()


class APIManager:
    '''
    Base class for REST API interaction. Handles common operations.
    '''

    def __init__(self):
        return

    def login(
        self,
        token=None,
        dry_run=False,
        api_base='https://singlecell.broadinstitute.org/single_cell/api/v1/',
    ):
        """
        Authenticates as user and get's token to perform actions on the user's behalf.

        :param token: User token to use with API
        :param dry_run: If true, will do a dry run with no actual execution of functionality.
        :param api_base: Domain of desired API environment
        :return: Boolean indicating of success or failure
        """

        ## TODO add in auth from a file.
        if self.verbose:
            print("LOGIN")
        if token is None:
            token = self.do_browser_login(dry_run=dry_run)
        self.token = token
        self.api_base = api_base
        self.verify_https = 'localhost' not in api_base and 'staging' not in api_base
        self.studies = None

    def do_browser_login(self, dry_run=False):
        '''
        Authenticate through the browser

        :param dry_run: If true, will do a dry run with no actual execution of functionality.
        :return: Authentication token
        '''

        if self.verbose:
            print("BROWSER LOGIN")
        if dry_run:
            if self.verbose:
                print("DRY_RUN:: Did not login")
            return "DRY_RUN_TOKEN"
        cmdline.func_CMD(command="gcloud auth application-default login")
        cmd_ret = cmdline.func_CMD(
            command="gcloud auth application-default print-access-token", stdout=True
        )
        return cmd_ret.decode("ASCII").strip(os.linesep)

    def do_get(self, command, dry_run=False):
        '''
        Perform a GET.

        :param command: String GET command to send to the REST endpoint
        :param dry_run: If true, will do a dry run with no actual execution of functionality.
        :return: Dict with response and status code
        '''

        ## TODO add timeout and exception handling (Timeout exeception)
        if self.verbose:
            print("DO GET")
            print(command)
        if dry_run:
            return {c_SUCCESS_RET_KEY: True, c_CODE_RET_KEY: c_API_OK}
        head = {'Accept': 'application/json'}
        if hasattr(self, 'token'):
            head[c_AUTH] = 'Bearer {}'.format(self.token)

        return self.check_api_return(
            requests.get(command, headers=head, verify=self.verify_https)
        )

    def do_post(self, command, values, files=None, dry_run=False):
        '''
        *** In development ***
        Perform POST.

        :param command: String POST command to send to the REST endpoint.
        :param values: Parameter values to send {name: value}
        :param files:
        :param dry_run: If true, will do a dry run with no actual execution of functionality.
        :return: Dict with response and status code
        '''

        ## TODO addtimeout and exception handling (Timeout exeception)
        if self.verbose:
            print("DO POST")
            print(command)
            print(values)
            print(files)
        if dry_run:
            print("DRY_RUN:: Returning success.")
            return {c_SUCCESS_RET_KEY: True, c_CODE_RET_KEY: c_API_OK}
        head = {c_AUTH: 'token {}'.format(self.token), 'Accept': 'application/json'}
        if self.verbose:
            print(head)
        if files is None:
            return self.check_api_return(
                requests.post(
                    command, headers=head, json=values, verify=self.verify_https
                )
            )
        else:
            return self.check_api_return(
                requests.post(
                    command,
                    headers=head,
                    files=files,
                    json=values,
                    verify=self.verify_https,
                )
            )

    def do_patch(self, command, values, dry_run=False):
        '''
        Perform PATCH

        :param command: String PATCH command to send to the REST endpoint
        :param values: Parameter values to send {name: value}
        :param dry_run: If true, will do a dry run with no actual execution of functionality.
        :return: Dict with response and status code/status
        '''

        ## TODO add timeout and exception handling (Timeout exeception)
        if self.verbose:
            print("DO PATCH")
            print(command)
            print(values)
        if dry_run:
            return {c_SUCCESS_RET_KEY: True, c_CODE_RET_KEY: c_API_OK}
        head = {c_AUTH: 'token {}'.format(self.token), 'Accept': 'application/json'}
        return self.check_api_return(
            requests.patch(command, headers=head, json=values, verify=self.verify_https)
        )

    def do_delete(self, command, dry_run=False):
        '''
        Perform Delete

        :param command: String DELETE command to send to the REST endpoint
        :param dry_run: If true, will do a dry run with no actual execution of functionality.
        :return: Dict with response and status code/status
        '''

        ## TODO add timeout and exception handling (Timeout exeception)
        if self.verbose:
            print("DO DELETE")
            print(command)
        if dry_run:
            return {c_SUCCESS_RET_KEY: True, c_CODE_RET_KEY: c_DELETE_OK}
        head = {c_AUTH: 'token {}'.format(self.token), 'Accept': 'application/json'}
        return self.check_api_return(
            requests.delete(command, headers=head, verify=self.verify_https)
        )

    def check_api_return(self, ret):
        '''
        Create dict that has if status code was successful, status code,and response

        :param ret: Response
        :return: Dict of response, status code, and status.
        '''

        if self.verbose:
            print(f'HTTP response status {ret.status_code}: {ret.reason}')
        api_return = {}
        api_return[c_SUCCESS_RET_KEY] = ret.status_code in [c_API_OK, c_DELETE_OK]
        if ret.status_code not in [c_API_OK, c_DELETE_OK]:
            print(f'Error {ret.status_code}: {ret.reason}')
            if ret.status_code == 401:
                print('')
                print(
                    'Are you still signed in?  SCP automatically logs you out after a period of inactivity.'
                )
                print('Try logging in and re-assigning your access token like so:')
                print('')
                print('\tgcloud auth login')
                print('\tACCESS_TOKEN=`gcloud auth print-access-token`')
                print('')
        api_return[c_CODE_RET_KEY] = ret.status_code
        api_return[c_RESPONSE] = ret
        return api_return

    def get_boundary(self):
        '''
        Creates a random string that is likely to not be in a MIME message. Used as a boundary between MIME parts.

        :return: String
        '''

        base = string.ascii_lowercase + string.digits
        return "".join([random.choice(base) for i in range(c_BOUNDARY_LENGTH)])


# The expected header
class SCPAPIManager(APIManager):
    '''
    API manager for the Single Cell Portal REST API
    '''

    def __init__(self, verbose=False):
        '''
        Initialize for the SCP endpoint.
        '''

        APIManager.__init__(self)
        self.verbose = verbose
        self.api_base = None  # set in APIManager.login()
        self.studies = None
        self.name_to_id = None
        self.bucket_id = None

        if self.verbose:
            print("INIT")

            logging.basicConfig()
            logging.getLogger().setLevel(logging.DEBUG)
            requests_log = logging.getLogger("requests.packages.urllib3")
            requests_log.setLevel(logging.DEBUG)
            requests_log.propagate = True
        else:
            # Disable warning seen on localhost due to self-signed SSL certificate
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # TODO: Hit the taxons API endpoint to get the list of available species.
        # self.species_genomes = {"cat":["felis_catus_9.0","felis_catus_8.0","felis_catus-6.2"]}

    @staticmethod
    def describe_status_code(status_code):
        '''
        Translate the status code to the text message, per SCP REST API documentation.

        :param status_code: Numeric status code to translate
        :return: String status code text
        '''

        ret_status_codes = {
            c_STUDY_EXISTS: c_STUDY_EXISTS_TEXT,
            c_STUDY_DOES_NOT_EXIST: c_STUDY_DOES_NOT_EXIST_TEXT,
            c_INVALID_STUDY_NAME: c_INVALID_STUDY_NAME_TEXT,
            c_INVALID_SHARE_MODE: c_INVALID_SHARE_MODE_TEXT,
            c_INVALID_SHARE_MISSING: c_INVALID_SHARE_MISSING_TEXT,
            c_INVALID_STUDY_DESC: c_INVALID_STUDY_DESC_TEXT,
            c_ATTRIBUTE_DOES_NOT_EXIST: c_ATTRIBUTE_DOES_NOT_EXIST_TEXT,
            c_NO_ERROR: c_NO_ERROR_TEXT,
            c_API_OK: c_NO_ERROR_TEXT,
            c_DELETE_OK: c_NO_ERROR_TEXT,
            c_API_AUTH: c_API_AUTH_TEXT,
            c_API_SYNTAX_ERROR: c_API_SYNTAX_ERROR_TEXT,
            c_API_AUTH_STUDY: c_API_AUTH_STUDY_TEXT,
            c_API_UNKNOWN_STUDY: c_API_UNKNOWN_STUDY_TEXT,
            c_API_CONTENT_HEADERS: c_API_CONTENT_HEADERS_TEXT,
            c_API_INVALID_STUDY: c_API_INVALID_STUDY_TEXT,
            c_API_BACKEND_ERROR: c_API_BACKEND_ERROR_TEXT,
        }
        return ret_status_codes.get(status_code, "That status code is not in use.")

    '''
    def check_species_genome(self, species, genome=None):
        """The SCP only support certain species, this checks the submitted species to make sure it is supported.

        :param species: String species to confirm is supported.
        :param genome: String, if provided optionally checks genome version.
        :return: Boolean, false indicates not supported.
        """

        print("CHECK SPECIES (GENOME)")
        if not species.lower() in self.species_genomes:
            print(species+" : this species is not registered with the portal please email the team to have it added.")
            return(False)
        return(genome in self.species_genomes[species])
    '''

    def get_studies(self, dry_run=False):
        '''
        Get studies available to user.

        :param dry_run: If true, will do a dry run with no actual execution of functionality.
        :return: Response
        '''

        if self.verbose:
            print("GET STUDIES")
        resp = self.do_get(self.api_base + "studies", dry_run=dry_run)
        if dry_run:
            print("DRY_RUN:: Returned dummy names.")
            resp[c_STUDIES_RET_KEY] = ["DRY_RUN 1", "DRY_RUN 2"]
        else:
            if resp[c_SUCCESS_RET_KEY]:
                studies_json = resp[c_RESPONSE].json()
                self.study_objects = studies_json
                self.studies = [str(element['name']) for element in studies_json]
                self.name_to_id = [
                    [str(element['name']), str(element['_id']['$oid'])]
                    for element in studies_json
                ]
                self.name_to_id = {key: value for (key, value) in self.name_to_id}
                resp[c_STUDIES_RET_KEY] = self.studies
        return resp

    def is_valid_study_description(self, study_description):
        '''
        Confirms a study description does not contain characters that are not allowed.

        :param study_description: String description
        :return: Boolean indicator of validity, True is valid
        '''

        no_error = True
        for letter in study_description:
            if letter in c_INVALID_STUDYDESC_CHAR:
                print(
                    "The following letter is not valid in a study description:'"
                    + letter
                    + "'"
                )
                no_error = False
        return no_error

    def is_valid_study_name(self, study_name):
        '''
        Confirms a study name does not contain characters that are not allowed.

        :param study_name: String study name
        :return: Boolean indicator oc validity, True is valid
        '''

        no_error = True
        for letter in study_name:
            if not letter in c_VALID_STUDYNAME_CHAR:
                print(
                    "The following letter is not valid in a study name:'" + letter + "'"
                )
                no_error = False
        return no_error

    def create_study(
        self,
        study_name,
        study_description='Single Cell Genomics Study',
        branding=None,
        billing=None,
        is_public=True,
        dry_run=False,
    ):
        '''
        Create a study name using the REST API.
        Confirms the study does not exist before creating.
        Confirms name and description are valid.

        :param study_name: String study name
        :param study_description: String study description
        :param branding: String branding
        :param billing: String FireCloud Billing object
        :param is_public: Boolean indicator if the study should be public
        :param dry_run: If true, will do a dry run with no actual execution of functionality.
        :return: Response
        '''
        if self.verbose:
            print("CREATE STUDY:: " + study_name)
        # Study variable validation
        ## Study must not exist
        if self.study_exists(study_name=study_name, dry_run=dry_run):
            return {c_SUCCESS_RET_KEY: False, c_CODE_RET_KEY: c_STUDY_EXISTS}
        # Study name is restricted on letters
        if not self.is_valid_study_name(study_name):
            return {c_SUCCESS_RET_KEY: False, c_CODE_RET_KEY: c_INVALID_STUDY_NAME}
        # Study description should not have HTML
        if not self.is_valid_study_description(study_description):
            return {c_SUCCESS_RET_KEY: False, c_CODE_RET_KEY: c_INVALID_STUDY_DESC}

        # Make payload and do post
        study_data = {
            "study": {
                "name": study_name,
                "study_detail_attributes": {
                    "full_description": study_description
                },
                "public": is_public
            }
        }
        if not branding is None:
            study_data["firecloud_project"] = billing
        if not branding is None:
            study_data["branding_group_id"] = branding
        resp = self.do_post(
            command=self.api_base + "studies", values=study_data, dry_run=dry_run
        )
        # Update study list
        if resp[c_SUCCESS_RET_KEY] and not dry_run:
            self.get_studies()
        return resp

    def get_study_attribute(self, study_name, attribute, dry_run=False):
        '''
        Get a study attribute using the REST API.

        :param study_name: String study name
        :param attribute: String name of attribute to return
        :param dry_run: If true, will do a dry run with no actual execution of functionality.
        :return: Response
        '''
        if self.verbose:
            print("LOOKING AT " + study_name)
        # Error if the study does not exist
        if (
            not self.study_exists(study_name=study_name, dry_run=dry_run)
            and not dry_run
        ):
            return {c_SUCCESS_RET_KEY: False, c_CODE_RET_KEY: c_STUDY_DOES_NOT_EXIST}
        # Convert study name to study id
        study_id = self.study_name_to_id(study_name, dry_run=dry_run)

        ret_study = self.do_get(
            command=self.api_base + "studies/" + str(study_id), dry_run=dry_run
        )
        if dry_run:
            print("DRY_RUN:: Returned dummy attribute.")
            ret_study[c_ATTR_RET_KEY] = "DUMMY ATTRIBUTE"
        else:
            study = ret_study[c_RESPONSE].json()
            # Error if attribute is not available
            if attribute not in study:
                print('The requested study attribute is not available.')
                return {
                    c_SUCCESS_RET_KEY: False,
                    c_CODE_RET_KEY: c_ATTRIBUTE_DOES_NOT_EXIST,
                }
            ret_study[c_ATTR_RET_KEY] = study[attribute]

        return ret_study

    def edit_study_description(
        self, study_name, new_description, accept_html=False, dry_run=False
    ):
        '''
        Edit a study description using the REST API.
        Confirms the study exists.

        :param study_name: String study name
        :param new_description: String new study description to update study with
        :param accept_html: Boolean Whether to allow HTML characters and formatting
        :param dry_run: If true, will do a dry run with no actual execution of functionality.
        :return: Response
        '''
        if self.verbose:
            print("EDITING DESCRIPTION FOR " + study_name)
        # Error if the study does not exist
        if (
            not self.study_exists(study_name=study_name, dry_run=dry_run)
            and not dry_run
        ):
            return {c_SUCCESS_RET_KEY: False, c_CODE_RET_KEY: c_STUDY_DOES_NOT_EXIST}
        # Convert study name to study id
        study_id = self.study_name_to_id(study_name, dry_run=dry_run)

        # New study description should not have HTML
        # except when it needs to...
        if not accept_html and not self.is_valid_study_description(new_description):
            return {c_SUCCESS_RET_KEY: False, c_CODE_RET_KEY: c_INVALID_STUDY_DESC}

        description_info = {
            "study": {
                "study_id": study_id,
                "study_detail_attributes": {
                    "full_description": new_description
                }
            }
        }

        update_ret = self.do_patch(
            command=self.api_base + "studies/" + str(study_id),
            values=description_info,
            dry_run=dry_run,
        )

        return update_ret

    def get_study_external_resources(self, study_name, dry_run=False):
        '''
        Get a study's external resources using the REST API.

        :param study_name: String study name
        :param dry_run: If true, will do a dry run with no actual execution of functionality.
        :return: Response
        '''
        if self.verbose:
            print("LOOKING AT " + study_name)
        # Error if the study does not exist
        if (
            not self.study_exists(study_name=study_name, dry_run=dry_run)
            and not dry_run
        ):
            return {c_SUCCESS_RET_KEY: False, c_CODE_RET_KEY: c_STUDY_DOES_NOT_EXIST}
        # Convert study name to study id
        study_id = self.study_name_to_id(study_name, dry_run=dry_run)

        study_resources = self.do_get(
            command=self.api_base + "studies/" + str(study_id) + "/external_resources",
            dry_run=dry_run,
        )
        if dry_run:
            print("DRY_RUN:: Returned dummy external resources.")
            study_resources[c_EXT_RET_KEY] = [
                {'_id': 'EXT_REC_DUMMY_1'},
                {'_id': 'EXT_REC_DUMMY_2'},
            ]
        else:
            resources = study_resources[c_RESPONSE].json()
            study_resources[c_EXT_RET_KEY] = resources

        return study_resources

    def delete_study_external_resource(self, study_name, resource_id, dry_run=False):
        '''
        Delete a study's external resource using the REST API.

        :param study_name: String study name
        :param resource_ids: String Id of external resource to delete
        :param dry_run: If true, will do a dry run with no actual execution of functionality.
        :return: Response
        '''
        if self.verbose:
            print("LOOKING AT " + study_name)
        # Error if the study does not exist
        if (
            not self.study_exists(study_name=study_name, dry_run=dry_run)
            and not dry_run
        ):
            return {c_SUCCESS_RET_KEY: False, c_CODE_RET_KEY: c_STUDY_DOES_NOT_EXIST}
        # Convert study name to study id
        study_id = self.study_name_to_id(study_name, dry_run=dry_run)
        ret_delete = self.do_delete(
            command=self.api_base
            + "studies/"
            + str(study_id)
            + "/external_resources/"
            + resource_id,
            dry_run=dry_run,
        )

        return ret_delete

    def create_study_external_resource(
        self, study_name, title, url, description, publication_url=False, dry_run=False
    ):
        '''
        Create an external resource for a study using the REST API.

        :param study_name: String study name
        :param title String title for resource
        :param url String URL for resource
        :param description String Tooltip description for resource
        :param publication_url Boolean Whether resource is publication
        :param dry_run: If true, will do a dry run with no actual execution of functionality.
        :return: Response
        '''
        if self.verbose:
            print("CREATING RESOURCE FOR " + study_name)
        # Error if the study does not exist
        if (
            not self.study_exists(study_name=study_name, dry_run=dry_run)
            and not dry_run
        ):
            return {c_SUCCESS_RET_KEY: False, c_CODE_RET_KEY: c_STUDY_DOES_NOT_EXIST}
        # Convert study name to study id
        study_id = self.study_name_to_id(study_name, dry_run=dry_run)

        # TODO: check whether resource already exists in some form
        # TODO: checks for formats of URL, description, etc
        # Make payload and do post
        resource_data = {
            "title": title,
            "url": url,
            "description": description,
            "publication_url": publication_url,
        }

        resp = self.do_post(
            command=self.api_base + "studies/" + str(study_id) + "/external_resources",
            values=resource_data,
            dry_run=dry_run,
        )

        return resp

    def set_permission(
        self, study_name, email, access, deliver_email=False, dry_run=False
    ):
        '''
        Sets permission on a study.

        :param study_name: String study name to update permissions
        :param email: String email (user) to update permission
        :param access: String access level for permission
        :param deliver_email: Boolean, is the user interested in email notifications for study changes (True, receive emails)
        :param dry_run: If true, will do a dry run with no actual execution of functionality
        :return: Dict with response and additional information including status and errors
        '''
        if self.verbose:
            print("SET PERMISSION: ".join(str(i) for i in [study_name, email, access]))
        # Make sure the access value is valid
        if not access in c_PERMISSIONS:
            return {c_SUCCESS_RET_KEY: False, c_CODE_RET_KEY: c_INVALID_SHARE_MODE}
        # Error if the study does not exist
        if (
            not self.study_exists(study_name=study_name, dry_run=dry_run)
            and not dry_run
        ):
            return {c_SUCCESS_RET_KEY: False, c_CODE_RET_KEY: c_STUDY_DOES_NOT_EXIST}
        # Convert study name to study id
        studyId = self.study_name_to_id(study_name, dry_run=dry_run)

        # Get the share id for the email
        ret_shares = self.do_get(
            command=self.api + "studies/" + str(studyId) + "/study_shares",
            dry_run=dry_run,
        )
        share_id = None
        for share in ret_shares[c_RESPONSE].json():
            if share["email"] == email:
                share_id = share['_id']['$oid']

        permissions_info = {
            "study_id": studyId,
            "study_share": {
                "email": email,
                "permission": access,
                "deliver_emails": deliver_email,
            },
        }
        if share_id is None:
            # Delete share
            if access == c_ACCESS_REMOVE:
                return {
                    c_SUCCESS_RET_KEY: False,
                    c_CODE_RET_KEY: c_STUDY_DOES_NOT_EXIST,
                }
            # Set shares for study given it does not exist
            ret = self.do_post(
                command=self.api + "studies/" + str(studyId) + "/study_shares",
                values=permissions_info,
                dry_run=dry_run,
            )
            return ret
        else:
            # Delete share
            if access == c_ACCESS_REMOVE:
                ret_delete = self.do_delete(
                    command=self.api
                    + "studies/"
                    + str(studyId)
                    + "/study_shares/"
                    + share_id,
                    dry_run=dry_run,
                )
                return ret_delete
            # Update shares for a study that has the shares
            update_ret = self.do_patch(
                command=self.api
                + "studies/"
                + str(studyId)
                + "/study_shares/"
                + share_id,
                values=permissions_info,
                dry_run=dry_run,
            )
            return update_ret

    def study_exists(self, study_name, dry_run=False):
        '''
        Indicates if the user has access to a study of the given name

        :param study_name: String study name
        :param dry_run: If true, will do a dry run with no actual execution of functionality
        :return: Boolean, True indicates the study is known to the user and exists
        '''
        if self.verbose:
            print("STUDY EXISTS?")
        if self.studies is None:
            ret = self.get_studies(dry_run=dry_run)
            if not ret[c_SUCCESS_RET_KEY]:
                return False
                #### TODO throw exception
        if dry_run:
            return True
        return study_name in self.studies

    def study_name_to_id(self, name, dry_run=False):
        '''
        Changes the a study name into the correct a portal id

        :param name: String study name
        :param dry_run: If true, will do a dry run with no actual execution of functionality.
        :return: String portal id
        '''
        if self.verbose:
            print("STUDY NAME TO ID")
        if dry_run:
            print("DRY_RUN:: returning a dummy id")
            return "1"
        else:
            return self.name_to_id.get(name, None)

    @staticmethod
    def upload_via_gsutil(bucket_id, file_path):
        """Copy file to Google Cloud Storage bucket, return stats and filename
        """

        gs_url = 'gs://' + bucket_id

        # Upload to bucket via gsutil
        command = 'gsutil cp ' + file_path + ' ' + gs_url
        cmdline.func_CMD(command=command)
        filename = file_path.split('/')[-1]

        # Get GCS details for the file just uploaded
        command = 'gsutil stat ' + gs_url + '/' + filename
        stdout = cmdline.func_CMD(command=command, stdout=True)

        # Split on newline, omit first and last lines, transform to dict
        lines = [line.strip() for line in str(stdout).split('\\n')][1:-1]
        gsutil_stat = {}
        for line in lines:
            [key, value] = line.split(':    ')
            gsutil_stat[key] = value.strip()

        return [gsutil_stat, filename]

    def upload_study_file(
        self,
        file,
        file_type,
        study_name,
        name=None,
        description="",
        parse=False,
        dry_run=False,
        **kwargs,
    ):
        """Wrapper for study file upload.

        Upload via gsutil, then point SCP to resulting object in bucket.
        """

        # Error if the study does not exist
        if (
            not self.study_exists(study_name=study_name, dry_run=dry_run)
            and not dry_run
        ):
            return {c_SUCCESS_RET_KEY: False, c_CODE_RET_KEY: c_STUDY_DOES_NOT_EXIST}
        # Convert study name to study id

        # python manage_study.py --env development --token=`gcloud auth print-access-token` upload-cluster --file ../demo_data/cluster_example.txt --study apitest --cluster-name test-cluster --species "Felis catus" --genome "Felis_catus_9.0"
        study_id = self.study_name_to_id(study_name, dry_run=dry_run)

        for s in self.study_objects:
            if s['_id']['$oid'] == study_id:
                study = s
                break
        bucket_id = study['bucket_id']

        [gsutil_stat, filename] = self.upload_via_gsutil(bucket_id, file)

        file_fields = {
            'study_file': {
                'file_type': file_type,
                'name': name,
                'remote_location': filename,
                'upload_file_name': filename,
                'upload_content_type': gsutil_stat['Content-Type'],
                'upload_file_size': int(gsutil_stat['Content-Length']),
                'generation': gsutil_stat['Generation'],
            }
        }
        for kwarg in kwargs:
            # Handles file-type specific fields, e.g. "species" and "genome"
            # for expression matrix files
            file_fields['study_file'][kwarg] = kwargs[kwarg]

        ret = self.do_post(
            command=self.api_base + 'studies/' + study_id + '/study_files',
            values=file_fields,
            dry_run=dry_run,
        )
        # print(f'/study_files response: {ret["response"].text}')

        if parse:
            study_files_response = ret['response'].json()
            study_file_id = study_files_response['_id']['$oid']
            parse = (
                f'{self.api_base}studies/{study_id}/study_files/{study_file_id}/parse'
            )
            ret = self.do_post(command=parse, values=None, dry_run=dry_run)
            # print(f'/parse response: {ret["response"].text}')

        return ret

    def upload_metadata(
        self, file, study_name, description="", use_convention=False, dry_run=False
    ):
        if self.verbose:
            print("UPLOAD METADATA FILE")
        return self.upload_study_file(
            file,
            'Metadata',
            study_name,
            description=description,
            parse=True,
            use_metadata_convention=use_convention,
            dry_run=dry_run,
        )

    def upload_expression_matrix(
        self, file, study_name, species=None, genome=None, description="", dry_run=False
    ):
        if self.verbose:
            print("UPLOAD EXPRESSION MATRIX FILE")
        return self.upload_study_file(
            file,
            'Expression Matrix',
            study_name,
            description=description,
            species=species,
            genome=genome,
            parse=True,
            dry_run=dry_run,
        )

    def upload_cluster(
        self,
        file,
        study_name,
        cluster_name,
        description="",
        x="X",
        y="Y",
        z="Z",
        dry_run=False,
    ):
        if self.verbose:
            print("UPLOAD CLUSTER FILE")
        return self.upload_study_file(
            file,
            'Cluster',
            study_name,
            cluster_name=cluster_name,
            description=description,
            x=x,
            y=x,
            z=x,
            parse=True,
            dry_run=dry_run,
        )


class DSSAPIManager(APIManager):
    '''
    API manager for the HCA DSS
    '''

    def __init__(self):
        '''
        Initialize for the DSS endpoint
        '''

        APIManager.__init__(self)
        if self.verbose:
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

    def describe_status_code(status_code):
        '''
        Translate the status code to the text errors as per their endpoint documentation.

        :param status_code: Numeric status code to translate
        :return: String status code text
        '''

        ret_status_codes = {
            c_MATRIX_API_OK: c_NO_ERROR_TEXT,
            c_MATRIX_REQUEST_API_OK: c_NO_ERROR_TEXT,
            c_MATRIX_BAD_FORMAT: c_MATRIX_BAD_FORMAT_TEXT,
            c_API_SYNTAX_ERROR: c_API_SYNTAX_ERROR_TEXT,
        }
        return ret_status_codes.get(status_code, "That status code is not in use.")

    def get_supported_types(self, dry_run=False):
        '''
        Query and update supported file types for delivery by the matrix service

        :param dry_run: If true, will do a dry run with no actual execution of functionality
        :return: Returns the response, also updates the supported types (in the Matrix Manager)
        '''
        print("GET SUPPORTED TYPES")
        if dry_run:
            self.supportedTypes = ["test_type", "test_type"]
            return {c_SUCCESS_RET_KEY: True}
        if self.supportedTypes is None:
            resp = self.do_get(self.api + "formats")
            if resp[c_SUCCESS_RET_KEY]:
                self.supportedTypes = resp[c_RESPONSE].json()
        return resp

    def request_matrix(self, ids, format="zarr", dry_run=False):
        '''
        *** In development ****
        Request a matrix by supplying bundle IDs

        :param ids: HCA bundle ids
        :param format: String supported file format to format the matrix to be received
        :param dry_run: If true, will do a dry run with no actual execution of functionality.
        :return: Response
        '''
        print("REQUEST MATRIX BY IDs")
        if not format in self.get_supported_types():
            return {c_SUCCESS_RET_KEY: False, c_CODE_RET_KEY: c_MATRIX_BAD_FORMAT}
        bundleInfo = {"bundle_fqids": ids, "format": format}
        resp = self.do_post(self.api, values=bundleInfo, dry_run=dry_run)
        return resp

