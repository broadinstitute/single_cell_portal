# -*- coding: utf-8 -*-

import requests

# Constants
c_AUTH = 'Authorization'
# The expected header
class StudyManager:

    def __init__(self):
        print("INIT")
        self.api = "https://portals.broadinstitute.org/single_cell/api/v1/"

    def login(self, token):
        """
        :param token: User token to use with API
        :return: Boolean Indicator of success or failure (False)
        """
        print("LOGIN")
        self.token = token


    def do_get(self, command):
        print("DO GET")
        print(command)
        head = {c_AUTH:'token {}'.format(self.token),
                'Accept':'application/json'}
        print(str(head))
        r = requests.get(command, headers=head)
        if r.status_code != 200:
            raise BaseException(str(r))
        return(r)

    def get_studies(self):
        print("GET STUDIES")
        resp = self.do_get(self.api + "studies")
        return([str(element.get('name')) for element in resp.json()])



c_token = ''
test = StudyManager()
test.login(c_token)
print(test.get_studies())
