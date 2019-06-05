import hashlib
import hmac
import logging
import os

import requests

log = logging.getLogger(__name__)


class SlackClient:
    BASE_URL = "https://slack.com/api/"

    def __init__(self, token: str):
        self.session = requests.session()
        self.token = token

        self.session.headers.update(
            {
                'Authorization': 'Bearer ' + self.token,
                'Content-Type': 'application/json; charset=utf8'
            })

    def _api_post(self, method_name: str, payload: dict):
        url = self.BASE_URL + method_name
        response = self.session.post(url, json=payload)
        response.raise_for_status()

        return response.json()

    def chat_send_message(self, text: str, recipient: str):
        payload = {
            'username': 'Sqdc Trigger Notifications',
            'channel': '@{}'.format(recipient),
            'text': text
        }
        return self._api_post('chat.postMessage', payload)

    @staticmethod
    def verify_slack_request(slack_signature, slack_request_timestamp, request_body):
        slack_secret = os.environ["SLACK_SIGNING_SECRET"]
        print(slack_signature)

        ''' Form the basestring as stated in the Slack API docs. We need to make a bytestring. '''
        basestring = f"v0:{slack_request_timestamp}:{request_body}".encode('utf-8')

        ''' Make the Signing Secret a bytestring too. '''
        slack_signing_secret = bytes(slack_secret, 'utf-8')

        ''' Create a new HMAC "signature", and return the string presentation. '''
        my_signature = 'v0=' + hmac.new(slack_signing_secret, basestring, hashlib.sha256).hexdigest()

        ''' Compare the the Slack provided signature to ours.
        If they are equal, the request should be verified successfully.
        Log the unsuccessful requests for further analysis
        (along with another relevant info about the request). '''
        if hmac.compare_digest(my_signature, slack_signature):
            return True
        else:
            log.warning(f"Verification failed. my_signature: {my_signature}")
            return False

