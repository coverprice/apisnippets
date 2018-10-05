#!/bin/env python3

class UserToCreate(object):
    """
    This is a data object that stores info on a user to be created in AWS, and also records progress
    of that process (e.g. contains pre-flight check errors that occur during validation)
    """
    def __init__(self,
            user_id : str,          # This is either the Kerberos ID or an email address
            gpg_key : str = None,   # ASCII-armored GPG key (or None for plaintext)
            output_file=None,       # File path for output (or None for stdout)
        ):
        self.user_id = user_id
        self.gpg_key = gpg_key
        self.output_file = output_file

        self.kerberos_id = None
        self.email = None
        self.output_message = None

        self.errors = []

    def add_error(self, error : str):
        self.errors.append(error)

    def has_errors(self):
        return len(self.errors) > 0
