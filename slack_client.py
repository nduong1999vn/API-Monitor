
import time
import logging
from config import Config
import requests
import json
logging.basicConfig(format="%(asctime)s %(name)s %(levelname)s %(message)s", level=logging.INFO)

class Slack():
    def __init__(self, config_file, log_level=logging.INFO) :
        self.config = Config(config_file)
        self.message_api = self.config.get("slack", "slack.message.api") 
        self.slack_external_message_api = self.config.get("slack", "slack.external.message.api") 
        self.slack_token = self.config.get("slack", "slack.token") 
        self.slack_channel = "#" + self.config.get("slack", "slack.channel") 
        self.slack_icon_url = self.config.get("slack", "slack.icon_url") 
        self.slack_user_name = self.config.get("slack", "slack.username") 
        self.log = logging.getLogger(self.__class__.__name__)
        self.log.setLevel(log_level)
        self.log.info('slack_channel is {}'.format(self.slack_channel))
    
    def post_message_to_slack(self, text, blocks = None):

        tm = time.strftime('%a, %d %b %Y %H:%M:%S %Z(%z)')
        text = "{}: {}".format(tm, text)
        data = {'text': text}
        res = requests.post(self.slack_external_message_api, data=json.dumps(data))
        self.log.info('post_message_to_slack is {}'.format(text))
        self.log.info('Cannot get json from response: %s, status code: %s', res.text, res.status_code)
        return None

    def user_post_message_to_slack(self, text, blocks = None):

        tm = time.strftime('%a, %d %b %Y %H:%M:%S %Z(%z)')
        text = "{}: {}".format(tm, text)
        return requests.post(self.message_api, {
            'token': self.slack_token,
            'channel': self.slack_channel,
            'text': text,
            'icon_url': self.slack_icon_url,
            'username': self.slack_user_name,
            'blocks': json.dumps(blocks) if blocks else None
        }).json()