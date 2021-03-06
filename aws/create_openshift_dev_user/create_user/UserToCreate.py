#!/bin/env python3

from enum import Enum
class UserCreateStatus(Enum):
    AWAITING_PREFLIGHT_CHECK = 1
    FAILED_PREFLIGHT_CHECK = 2
    READY_TO_CREATE = 3
    ACCOUNT_CREATED = 4
    FAILED_TO_CREATE_ACCOUNT = 5


class UserToCreate(object):
    """
    This is a data object that stores info on a user to be created in AWS, and also records progress
    of that process (e.g. contains pre-flight check errors that occur during validation)
    """
    def __init__(self,
            user_id : str,          # This is either the Kerberos ID or an email address
            gpg_key : str = None,   # ASCII-armored GPG key (or None for plaintext)
            spreadsheet_row=None,   # The row number from the spreadsheet that this user record came from
        ):
        self.status = UserCreateStatus.AWAITING_PREFLIGHT_CHECK
        self.user_id = user_id
        self.gpg_key = gpg_key
        self.spreadsheet_row = spreadsheet_row

        self.kerberos_id = None
        self.email = None
        self.output_message = None

        self.errors = []

    def add_error(self, error : str):
        self.errors.append(error)

    def has_errors(self):
        return len(self.errors) > 0
