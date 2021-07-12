
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
import json
from application_client import Application, RestClient, AuthClient

# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait

from slack_client import Slack
from email_client import EmailClient

from config import Config
logging.basicConfig(format="%(asctime)s %(name)s %(levelname)s %(message)s", level=logging.INFO)


import time, threading
class SetInterval(object):
    def __init__(self,interval, duration, action) :
        self.interval=interval
        self.action=action
        self.duration=duration
        # self.params=params
        self.log = logging.getLogger(self.__class__.__name__)
        self.log.setLevel(logging.INFO)

        self.stop_event=threading.Event()
        thread=threading.Thread(target=self.__set_interval)
        thread.start()
        # Wait for at most 30 seconds for the thread to complete.
        thread.join(duration)
        # Always signal the event. Whether the thread has already finished or not, 
        # the result will be the same.
        self.stop_event.set()
        # Now join without a timeout knowing that the thread is either already 
        # finished or will finish "soon."
        thread.join()

    def __set_interval(self) :
        next_time=time.time()+self.interval
        while not self.stop_event.wait(next_time-time.time()) :
            next_time+=self.interval
            # validation_link = self.action(self.params)
            validation_link = self.action()
            if validation_link is not None:
                self.log.info('validation_link is {}'.format(validation_link))
                self.cancel()

    def cancel(self) :
        self.stop_event.set()
        
class Monitor():
    def __init__(self, config_file, log_level=logging.INFO) :
        self.config_file = config_file
        self.config = Config(config_file)
        self.admin_account = self.config.get("login", "login.test.email") 
        self.admin_pass = self.config.get("login", "login.test.password")

        self.monitor_account = self.config.get("monitor", "monitor.account") 
        self.monitor_server = self.config.get("monitor", "imap.server")
        self.monitor_pass = self.config.get("monitor", "monitor.password")
        self.application_monitor_pass = self.monitor_pass
        self.required_sender = self.config.get("validation", "email.sender")
        self.required_subject = self.config.get("validation", "email.subject")
        self.email_client = EmailClient(config_file)
        self.slack = Slack(config_file)

        self.log = logging.getLogger(self.__class__.__name__)
        self.log.setLevel(log_level)

    def delete_monitor_account(self, warning=True):
        client = AuthClient(self.config_file)
        payload = {
            "email": self.admin_account,
            "password": self.admin_pass
            }
        if not client.login(payload) and warning:     
            self.slack.post_message_to_slack("Problem with Login API")    
        # # Delete user
        res = client.delete_user(self.monitor_account)
        if not self.is_response_ok(res) and warning:
            self.slack.post_message_to_slack("Delete User API error!")

    def monitor_registration(self, duration, interval):

        self.email_client.delete_all_email()

        client = AuthClient(self.config_file)
        # Perform health check on the server
        server_status = client.health_check()
        if server_status == "OK":
            # I. Use the client to do the monitoring
            payload =     {
                "email": self.monitor_account,
                "fullName": "V-Space Monitor",
                "password": self.application_monitor_pass
                }
            # I.1 Register an user with email and password
            # self.delete_monitor_account(warning=False)
            res = client.register(payload)
            # print (res)
            self.log.info('register response is {}'.format(res))

            # # I.2 Check email to see if we got the email validation
            stop_time = time.time() + duration
            validation_link = None
            while time.time() < stop_time :
                validation_link = self.check_verification_email()
                if validation_link is not None:
                    self.log.info('validation_link is {}'.format(validation_link))
                    break
                time.sleep(interval)
            
            if validation_link is None:
                warning_subject = self.config.get("warning", "email.warning_subject") 
                warning_message = self.config.get("warning", "email.warning_message") 
                # self.email_client.send_email(warning_subject, warning_message, self.monitor_account)
                res = self.slack.post_message_to_slack(warning_message)
                # self.log.info('post_message_to_slack res :  {}'.format(res))
            else:
                self.delete_monitor_account()
        else: #System die
            warning_message = self.config.get("warning", "system.warning_message")
            warning_subject = self.config.get("warning", "email.warning_subject")  
            # self.email_client.send_email(warning_subject, warning_message, self.monitor_account)
            res = self.slack.post_message_to_slack(warning_message)
            
                
    def is_response_ok(self, res):
        self.log.info('is_response_ok : {}'.format(res))
        if 'statusCode' in res and res['statusCode'] == 200:
            return True
        return False

    def check_verification_email(self):
        
        self.log.info('Checking email for validation link')
        email_body = self.email_client.get_validation_email (self.required_sender, self.required_subject)
        validation_url = self.get_validation_link(email_body)
        # # 4 Request the link (just call the link) to validate the registration    
        if validation_url is not None:
            self.log.info('Validation url: {}'.format(validation_url))
#             #PROBLEM: Can not load the url because of javascript redirect
#             # prepare the option for the chrome driver
#             chrome_options = webdriver.ChromeOptions()
#             chrome_options.add_argument("--disable-extensions")

#             chrome_options.add_argument("--disable-popup-blocking")

#             chrome_options.add_argument("--profile-directory=Default")

#             chrome_options.add_argument("--ignore-certificate-errors")

#             chrome_options.add_argument("--disable-plugins-discovery")

#             chrome_options.add_argument("--incognito")

#             chrome_options.add_argument("user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:46.0) Gecko/20100101 Firefox/46.0'")

#             # options.add_argument('headless')
#             # start chrome browser
#             browser = webdriver.Chrome('./chromedriver_linux64_89/chromedriver', chrome_options=chrome_options)
#             browser.get(validation_url)

#             wait = WebDriverWait(browser, 30)
# #             # wait.until(lambda browser: browser.current_url != validation_url)
#             wait.until(lambda browser: browser.find_element_by_class_name("firebaseui-title"))

#             print("current_url", browser.find_element_by_id("actionElement").get_attribute('innerHTML'))
#             browser.quit()
        else:
            print("No URL found.")
            return validation_url

        # # Login : NOT YET because we still can not validate the link    
        # client = AuthClient(self.config_file)
        # payload = {
        #     "email": self.monitor_account,
        #     "password": self.application_monitor_pass
        #     }

        # client.login(payload)


        # #If the validation works, we can use the current validated user to login and to delete.
        # #The validation link does not work now so we use the default account to test the login and delete API        
        # # 6 Change password
        # # 7 Logout
        # # 8 Login again

        return validation_url

    def get_validation_link(self, body, regex = None):
        """ #regex = config.get("validation","validation.email.regex") """

        if body is None:
            return None

        if regex is None:
            regex = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        validation_link = re.search(regex, body)

        if validation_link:
            return validation_link.group(0)
        else:
            return None
    
    def monitor_authentification(self):

        client = AuthClient(self.config_file)
        # Perform health check on the server
        server_status = client.health_check()
        if server_status != "OK":
            warning_message = self.config.get("warning", "system.warning_message")
            warning_subject = self.config.get("warning", "email.warning_subject")  
            self.email_client.send_email(warning_subject, warning_message, self.monitor_account)
            res = self.slack.post_message_to_slack(warning_message)
            return

        # I. Use the client to do the monitoring
        payload =     {
            "email": self.admin_account,
            "password": self.admin_pass
            }

        if not client.login(payload):
            self.slack.post_message_to_slack("Problem with Login API") 
            
        if not client.logout():
            self.slack.post_message_to_slack("Problem with Logout API") 

        if not client.login_cms(payload):
            self.slack.post_message_to_slack("Problem with Login CMS API") 

        if not client.logout():
            self.slack.post_message_to_slack("Problem with Logout API") 
    

CONFIG_FILE = 'config/config-template.ini' # use your own config file

if __name__ == '__main__':
    print(sys.argv)
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    else:
        config_file = CONFIG_FILE

    monitor = Monitor(config_file)
    monitor.monitor_authentification()
    monitor.monitor_registration(15,2)

    # The code below is used to check the APIs regularly in a defined timeset
    # while True:
    #     monitor.monitor(15,2)
    #     monitor.monitor_authentification()
    #     time.sleep(600)
