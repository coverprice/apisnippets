#!/bin/env python3

"""
This file is for functions that hide the complexity of the Google API from higher-level classes
"""

import google.oauth2.service_account
import apiclient.discovery
import re

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
