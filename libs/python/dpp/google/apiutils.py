#!/bin/env python3

"""
This file is for functions that hide the complexity of the Google API from higher-level classes
"""

import google.oauth2.service_account
import apiclient.discovery
import re
from .auth import OAuth2TokenWorkflow

SHEETS_SCOPES_READ_ONLY = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SHEETS_SCOPES_READ_WRITE = ['https://www.googleapis.com/auth/spreadsheets']

def get_sheets_service(service_account_file, read_only=False):
    scopes = SHEETS_SCOPES_READ_ONLY if read_only else SHEETS_SCOPES_READ_WRITE
    credentials = google.oauth2.service_account.Credentials.from_service_account_file(
        service_account_file,
        scopes=scopes,
    )
    service = apiclient.discovery.build('sheets', 'v4', credentials=credentials)
    return service


GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.send']
def get_gmail_service(client_secret_file : str, refresh_token_file : str):
    """
    For more info on these params, see the auth/README.md
    @param client_secret_file - path to the Oauth2 client secret (downloadable from
                                [GCP Project] -> APIs & Services -> Credentials)
    @param refresh_token_file - path to a file to store the Refresh Token.
    """
    oauth2_token_workflow = OAuth2TokenWorkflow(
        client_secret_file=client_secret_file,
        refresh_token_file=refresh_token_file,
        scopes=GMAIL_SCOPES,
    )
    credentials = oauth2_token_workflow.get_credentials()
    return apiclient.discovery.build('gmail', 'v1', credentials=credentials)
