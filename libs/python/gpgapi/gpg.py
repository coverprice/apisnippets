#!/usr/bin/python3

# Installed from 'sudo dnf install python3-gnupg'
import gnupg
import sys
import tempfile
from pprint import pprint


class InvalidKeyException(Exception):
    pass


class EncryptionFailureException(Exception):
    pass


def encrypt(data, key):
    with tempfile.TemporaryDirectory() as gpg_home_dir:
        gpg = gnupg.GPG(gnupghome=gpg_home_dir)

        import_result = gpg.import_keys(key)

        #validate that there was just one key
        if import_result.count == 0:
            raise InvalidKeyException('No keys found during import')
        if import_result.count > 1:
            raise InvalidKeyException('Multiple keys found during import, must be exactly 1 key')

        # pprint(gpg.list_keys())
        if len(gpg.list_keys(True)):    # True means list private keys
            raise InvalidKeyException('This key includes the private key!'
                ' The user mistakenly supplied their public/private keypair!'
                ' They should only have supplied their public keypair.')

        encrypted_ascii_data = gpg.encrypt(
            data,
            recipients=[import_result.fingerprints[0]],
            always_trust=True,
        )
        if encrypted_ascii_data.ok == False:
            raise EncryptionFailureException('Failed to encrypt data: {}'.format(encrypted_ascii_data.status))

    return str(encrypted_ascii_data)
