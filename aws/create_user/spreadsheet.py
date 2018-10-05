#!/bin/env python3

from pprint import pprint
import sys
import os
import os.path
import tempfile
import subprocess
sys.path.append(os.path.join(os.path.dirname(__file__), 'libs', 'python'))
import googledocsapi.api

from .UserToCreate import UserToCreate

class GoogleSheetsDataBridge(object):
    def __init__(self,
            spreadsheet_id : str,
            service_account_file : str,
        ):
        self.spreadsheet_id = spreadsheet_id
        self.service = googledocsapi.api.getSheetsService(
            service_account_file=service_account_file,
            read_only=True,         # TODO change this when we implement updating the status
        )

    def get_users(self) -> list:
        result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='Form Responses 1!B2:I100',
            ).execute()
        values = result.get('values', [])
        if not values:
            return []

        users_to_create = []
        for row in values:
            if len(row) < 8:
                # (Probably) empty row
                continue

            # TODO - new rows are created with a blank column, not 'In Review'. In the post-run phase (or perhaps right now?) these should be updated
            # to be the default: 'In Review'
            status = row[7] if len(row) >= 8 else 'In Review'

            if status not in ['In Review', 'Approved-but-not-created']:
                continue

            email = row[0].lower().strip()
            if email == '':
                continue

            gpg_key = row[6]
            if "-----BEGIN PGP PUBLIC KEY BLOCK-----" not in gpg_key:
                gpg_key = None

            # TODO - if we want to update the user, we'll have to add the sheet row # into the object.
            users_to_create.append(UserToCreate(
                user_id=email,
                gpg_key=gpg_key,
                output_file=None,
            ))
        return users_to_create
