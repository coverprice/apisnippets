#!/usr/bin/python3

import urllib
import time
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import Flow
from pprint import pprint
import sys
import os.path


class OAuth2TokenWorkflow(object):
    def __init__(self,
            client_secret_file : str,     # Path to the Service Account's JSON credentials file
            refresh_token_file : str,       # Writeable file path to store the refresh token
            scopes : list,
        ):
        self.client_secret_file = client_secret_file
        self.refresh_token_file = refresh_token_file
        # self._credentials = None            # google.oauth2.credentials.Credentials

        if os.path.isfile(self.refresh_token_file):
            with open(self.refresh_token_file, 'r') as fh:
                self._refresh_token = fh.read().strip()
        else:
            self._refresh_token = None

        self._access_token = None
        self._access_token_expire_time = None   # Epoch time that the access token will expire

        self._flow = Flow.from_client_secrets_file(
            client_secrets_file=client_secret_file,
            scopes=['https://mail.google.com/'],
        )
        # Hardcoded dummy redirect URI for non-web apps.
        self._flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'


    def get_credentials(self):
        """
        @return google.oauth2.credentials.Credentials
        """
        if not self._is_valid_access_token():
            self._generate_new_access_token()
        return self._flow.credentials


    def _generate_new_access_token(self):
        # Use the Refresh token if we have one, otherwise ask the user for help in generating
        # a new refresh+access token.
        if self._refresh_token is None:
            # This will generate both a new refresh & access token
            self._generate_new_refresh_and_access_token()
            return

        assert(self._refresh_token is not None)

        # The format of this response is identical to the format returned by oauth2session.fetch_token,
        # which is detailed below.
        response = self._flow.oauth2session.refresh_token(
            token_url=self._flow.client_config['token_uri'],
            client_id=self._flow.client_config['client_id'],
            client_secret=self._flow.client_config['client_secret'],
            refresh_token=self._refresh_token,
        )
        self._refresh_token = response['refresh_token']
        self._set_new_token(
            access_token=response['access_token'],
            expires_in=int(response['expires_in']),
            refresh_token=response['refresh_token'],
        )


    def _set_new_token(self,
            access_token : str,
            expires_in : int,
            refresh_token : str,
        ):
        # Note: we use "$current_time + $expires_in" and not 'expires_at' returned by the response,
        # because the client's local clock may be out of sync.
        self._access_token = access_token
        self._access_token_expire_time = time.time() + int(expires_in)
        self._refresh_token = refresh_token
        with open(self.refresh_token_file, 'w') as fh:
            fh.write(self._refresh_token)


    def _is_valid_access_token(self):
        # the 120 seconds is for some wiggle-room
        return self._access_token is not None and time.time() < self._access_token_expire_time - 120


    def _generate_new_refresh_and_access_token(self):
        auth_url, _ = self._flow.authorization_url(prompt='consent')

        print('To authorize this application, visit this URL and follow the directions:')
        print('  {}'.format(auth_url))

        code = input('Enter verification code: ').strip()
        # Note: this call also stores the returned token in the self._flow.oauth2session object
        response = self._flow.fetch_token(code=code)
        """
        response typically looks like:
            {
                'access_token': '<some long secret string>',
                'expires_at': 1539234344.2879944,                   // Epoch time of expiry
                'expires_in': 3600,                                 // Seconds till expired
                'refresh_token': '<some long secret string>',       // Token used to get another access token when this expires.
                'scope': ['<list of scopes that the access token is for>'],
                'token_type': 'Bearer',
            }
        """
        self._set_new_token(
            access_token=response['access_token'],
            expires_in=int(response['expires_in']),
            refresh_token=response['refresh_token'],
        )
