import json
import logging
import urllib.request
from urllib.parse import urlencode
import os, sys
from urllib.parse import urljoin
import time
import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.header import decode_header
import re
import requests
from config import Config
logging.basicConfig(format="%(asctime)s %(name)s %(levelname)s %(message)s", level=logging.INFO)

class RestClient(object):

    def __init__(self, cookies=None, log_level=logging.INFO):
        self.cookies = cookies
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json;charset=UTF-8"
        }

        self.log = logging.getLogger(self.__class__.__name__)
        self.log.setLevel(log_level)

    def set_authorization(self, authorization=None):
        if authorization is not None:
            self.headers['authorization'] = authorization

    def processed_response(self, res, json_response=True):
        if json_response:
            try:
                return res.json()
            except:
                self.log.exception('Cannot get json from response: %s, status code: %s', res.text, res.status_code)
                return None
        else:
            return res

    def update_headers(self, headers):
        request_headers = dict(self.headers)
        if headers is not None:
            request_headers.update(headers)
        return request_headers

    def get(self, url, json_response=True, headers=None):
        self.log.debug("GET %s", url)
        res = requests.get(url, cookies=self.cookies, headers=self.headers)
        return self.processed_response(res, json_response)

    def post(self, url, payload, json_response=True, headers=None):
        json_payload = json.dumps(payload, indent=2)
        self.log.debug("POST %s\n%s\n%s", url, headers, json_payload)
        print("test post")
        headers = self.update_headers(headers)
        res = requests.post(url, cookies=self.cookies, data=json_payload, headers=headers)
        return self.processed_response(res, json_response)

    def put(self, url, payload, json_response=True, headers=None):
        json_payload = json.dumps(payload, indent=2)
        self.log.debug("PUT %s\n%s", url, json_payload)
        headers = self.update_headers(headers)
        res = requests.put(url, cookies=self.cookies, data=json_payload, headers=headers)
        return self.processed_response(res, json_response)

    def delete(self, url, json_response=True, headers=None):
        self.log.debug("DELETE %s", url)
        headers = self.update_headers(headers)
        res = requests.delete(url, cookies=self.cookies, headers=headers)
        return self.processed_response(res, json_response)


class Application(RestClient):
    """
    Python client to access backend API.
    """

    def __init__(self, config_file):
        super().__init__()
        self.config = Config(config_file)
        self.endpoint = self.config.get("url", "api.endpoint")

        authentication = self.get_authorization()
        self.set_authorization(authentication)

    def get_authorization(self):
        email = self.config.get("login", "login.test.email")
        password = self.config.get("login", "login.test.password")        

        login_payload = {
            "email": email,
            "password": password
        }

        res = self.authentication_login(login_payload)
        assert res and 'statusCode' in res and res['statusCode']==200, 'Cannot login with user email %s' % email
        self.log.info('Login success with user email %s' % email)

        access_token = res['data']['accessToken']
        authorization = 'Bearer ' + access_token
        return authorization

    def authentication_login(self, payload):
        url = self.endpoint + '/auth/login'
        res = self.post(url=url, payload=payload)
        return res
        
    # def check_user_email(self, email):
    #     payload = {}
    #     payload['email'] = email
    #     url = self.endpoint + '/authentication/_email_exist'
    #     return self.post(url, payload=payload)      

    # def signup(self, payload):
    #     self.log.info('signup with payload ', payload)
    #     res = self.check_user_email (payload['user_email'])
    #     if not res or 'success' not in res or not res['success'] or res['data']:
    #         self.log.info('user email is aready used')
    #         login_payload = {
    #             "email": payload['user_email'],
    #             "password": payload['password']
    #         }
    #         res = self.authentication_login(login_payload)
    #     else:
    #         url = self.endpoint + '/authentication/_register'
    #         res = self.post(url=url, payload=payload)
            
    #     print(res)
    #     assert res and 'success' in res and res['success'], 'Cannot signup or login with user email {}/{}'.format(payload['user_email'], payload['password'])
        
    #     self.log.info('login success')
    #     access_token = res['data']['access_token']
    #     authorization = 'Bearer ' + access_token
    #     self.set_authorization( authorization=authorization)

    #     return res

    def health_probe(self):
        url = self.endpoint + '/health_probe'
        return self.get(url)

    def health_check(self):
        url = self.endpoint + '/health_check'
        return self.get(url)

class AuthClient(RestClient):

    def __init__(self, config_file):
        super().__init__(log_level=logging.DEBUG)
        self.config = Config(config_file)
        self.endpoint = self.config.get("url", "api.endpoint") 
        self.auth_api = self.endpoint + '/auth'

    def register(self, payload):
        self.log.info('register: {}'.format(payload))
        url = self.auth_api + '/register'
        return self.post(url=url, payload=payload)

    def login(self, payload):
        url = self.endpoint + '/auth/login'
        res = self.post(url=url, payload=payload)

        # assert res and 'statusCode' in res and res['statusCode']==200, 'Cannot login with user ' + payload['email'] + '. Status code ' + str(res['statusCode']) + res['message']
        if not res or 'statusCode' not in res or res['statusCode']!=200:
            return False
        self.log.info('Login success with user email {}'.format(payload))

        access_token = res['data']['accessToken']
        authorization = 'Bearer ' + access_token
        self.set_authorization(authorization)
        self.log.info('authorization: {}'.format(authorization))
        return True

    def login_cms(self, payload):
        url = self.endpoint + '/auth/login-cms'
        res = self.post(url=url, payload=payload)

        # assert res and 'statusCode' in res and res['statusCode']==200, 'Cannot login with user ' + payload['email'] + '. Status code ' + str(res['statusCode']) + res['message']
        if not res or 'statusCode' not in res or res['statusCode']!=200:
            return False
        self.log.info('Login success with user email {}'.format(payload))

        access_token = res['data']['accessToken']
        authorization = 'Bearer ' + access_token
        self.set_authorization(authorization)
        self.log.info('authorization: {}'.format(authorization))
        return True

    def logout(self):
        url = self.endpoint + '/auth/logout'
        res = self.post(url=url, payload=None)
        self.log.info('res logout : {}'.format(res))
        if not res or 'statusCode' not in res or res['statusCode']!=200:
            return False
        return True

    def health_check(self):
        self.log.info('Health checking')
        url = self.endpoint + '/healthcheck_services'
        res = self.get(url)
        self.log.info('health_check res: {}'.format(res))
        return res["message"]

    def delete_user(self, email):
        user_id = self.get_user( email)
        url = self.endpoint + '/user/{}'.format(user_id)
        # Not use the default delete method because the API provided by TU does not include json body
        # self.headers has now "Content-Type": "application/json;charset=UTF-8"
        # res= self.delete(url=url)
        # return res

        headers = {}
        headers['Accept'] = self.headers['Accept']
        headers['authorization'] = self.headers['authorization']
        res = requests.delete(url, cookies=self.cookies, headers=headers)
        res = self.processed_response(res, True)
        self.log.info('delete_user res: {}'.format(res))
        return res

    def get_user(self, email):

        url = self.endpoint + '/user/list?page=1&perPage=10&email={}'.format(email)
        # url = self.endpoint + '/user/profile'
        res = self.get(url=url)
        self.log.info('get_user res: {}'.format(res))
        if 'data' not in res or len(res['data'])==0:
            return None
        return res['data'][0]['_id']

class ApplicationApi(Application):
    def __init__(self, config_file):
        super().__init__(log_level=logging.DEBUG)

    def get_company_list(self, request, page=1, per_page=10, s=None, order_by="createdAt", order="ASC", is_featured=None, co_technologies=None, co_country=None, co_stage=None, co_category=None):
        url_request = request + '?page=' + page + '&per_page=' + per_page + '&orderBy=' + order_by + '$order=' + order
        if s is not None:
            url_request += '&s=' + s
        if is_featured is not None:
            url_request += '&isFeatured=' + is_featured
        if co_technologies is not None:
            url_request += '&coTechnologies=' + co_technologies
        if co_country is not None:
            url_request += '&coCountry=' + co_country
        if co_stage is not None:
            url_request += '&coStage=' + co_stage
        if co_category is not None:
            url_request += '&coCategory=' + co_category
        url = self.endpoint + '/company/{}'.format(url_request)

        res = self.get(url=url)
        self.log.info('get_company_list res: {}'.format(res))

        return res['data']

    def get_company(self, _id):
        url = self.endpoint + '/company/{}'.format(_id)
        res = self.get(url=url)

        self.log.info('get_company res: {}'.format(res))
        return res['data']

    def put_company(self, _id, payload):
        url = self.endpoint + '/company/{}'.format(_id)
        res = self.put(url=url, payload=payload)

        self.log.info('put_company res: {}'.format(res))

        return res['message']

    def delete_company(self, _id):
        url = self.endpoint + '/company/{}'.format(_id)
        res = self.delete(url=url)

        self.log.info('delete_company res: {}'.format(res))

        return res['message']

    def get_company_guest(self, _id):
        url = self.endpoint + '/company/{}/guest'.format(_id)
        res = self.get(url=url)

        self.log.info('get_company_guest res: {}'.format(res))

        return res['data']

    def post_company(self, payload):
        url = self.endpoint + '/company/register'
        res = self.post(url=url, payload=payload)

        self.log.info('post_company res: {}'.format(res))

        return res['data'][0]['_id']

    # Add your own API routings here

