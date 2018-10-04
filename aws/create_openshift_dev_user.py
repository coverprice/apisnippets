#!/bin/env python3

"""
This script uses the AWS APIs to list all AWS accounts in the organization, and all IAM accounts (users) in each account.
It generates a CSV to stdout.

It relies on a "coreosinc" profile being available in ~/.aws/credentials, which should map to the Master Account (aka Root Account).
"""

import sys
import csv
from pprint import pprint
import argparse
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'libs/python'))
import awsapi
import ldapapi
import gpgapi

ACCOUNT_NAME = "openshift-dev"
TEMPLATE = """
AWS account: {alias} ({account_id})
URL: https://{alias}.signin.aws.amazon.com/console

Username: {username}
Initial password: {password}

Run the following to update your ~/.aws/config & ~/.aws/credentials files:

cat >> ~/.aws/config <<EOF
[profile {alias}]
region = us-east-1
output = text
EOF

cat >> ~/.aws/credentials <<EOF
[{alias}]
aws_access_key_id = {access_key_id}
aws_secret_access_key = {secret_access_key}
EOF
"""

def gen_credentials_message(aws_user_info, aws_account_id, account_alias):
    return TEMPLATE.format(
        alias=account_alias,
        account_id=aws_account_id,
        username=aws_user_info['username'],
        password=aws_user_info['password'],
        access_key_id=aws_user_info['access_key_id'],
        secret_access_key=aws_user_info['secret_access_key'],
    ).lstrip()


def parse_args():
    parser = argparse.ArgumentParser(description='Creates an AWS user account in the {} account'.format(ACCOUNT_NAME))
    parser.add_argument('username', action="store", help='Kerberos ID or email address of the user to add')
    parser.add_argument('--skip-ldap-check', action='store_true',
        help='Skips the LDAP lookup of the user. Only supported if a Kerberos ID is supplied as a username.')
    parser.add_argument('-k', '--keyfile', nargs='?', type=argparse.FileType('r'), default=None,
        help='GPG key file to import and encrypt with. (If not specified, output is unencrypted')
    parser.add_argument('-o', '--outfile', nargs='?', type=argparse.FileType('w'), default=sys.stdout,
        help='Output filename (default: stdout)')
    parser.add_argument('--skip-account-create', action='store_true',
        help="For debugging. Performs all non-AWS steps, but doesn't actually create the AWS account.")
    return parser.parse_args()


def verify_kerberos_id(user_param : str, skip_ldap_check : bool) -> str:
    """
    @param user_param - kerberos ID or email address
    @param skip_ldap_check - True to skip verifying a kerberos ID via LDAP
    @return the user's kerberos ID
    """
    is_email = '@' in user_param
    if is_email:
        if not user_param.endswith('@redhat.com'):
            raise Exception('Email addresses must end with @redhat.com')

    if skip_ldap_check:
        if is_email:
            raise Exception('--skip-ldap-check is not compatible with specifying an email address')
        return user_param

    user_searcher = ldapapi.UserSearcher()
    if is_email:
        user = user_searcher.find_by_email(user_param)
    else:
        user = user_searcher.find_by_uid(user_param)
    if user is None:
        raise Exception('Could not find user record "{}"'.format(user_param))
    return user.uid.lower()



class CreateUserWorkflow(object):
    def __init__(self, args, aws_user_factory, aws_account_id):
        """
        @param argparse.Namespace args
        @param awsapi.UserFactory aws_user_factory
        @param string aws_account_id - 12-digit account ID
        """
        self.args = args

        self.aws_user_factory = aws_user_factory
        self.aws_account_id = aws_account_id

        self.key = None
        if self.args.keyfile is not None:
            self.key = self.args.keyfile.read()

        self.kerberos_id = None

    def run(self):
        self._preflight_checks()

        aws_user_info = self.aws_user_factory.create_user(
            username=self.kerberos_id,
            group_names=["Dev"],
        )

        message = gen_credentials_message(
            aws_user_info,
            aws_session.get_account_id(),
            account_alias=ACCOUNT_NAME,
        )

        if self.key is not None:
            message = gpgapi.encrypt(message, self.key)

        args.outfile.write(message)
        return


    def _preflight_checks(self):
        self.kerberos_id = verify_kerberos_id(
            user_param=self.args.username.lower().strip(),
            skip_ldap_check=self.args.skip_ldap_check,
        )
        if self.key:
            try:
                gpgapi.encrypt('blah blah blah', self.key)
            except gpgapi.ApiException:
                raise


class FakeUserFactory(object):
    """Replaces AWS UserFactory for use in tests"""
    def create_user(self, username, group_names=[]):
        return {
            'username': username,
            'password': 'abc123',
            'access_key_id': 'some_access_key_id',
            'secret_access_key': 'some_secret_access_key',
        }

aws_session = awsapi.AwsSession.for_profile(profile_name=ACCOUNT_NAME)
aws_account_id = aws_session.get_account_id()

args = parse_args()
if args.skip_account_create:
    aws_user_factory = FakeUserFactory()
else:
    aws_user_factory = awsapi.UserFactory(awsapi.IamOperations.for_session(aws_session.session))

CreateUserWorkflow(args, aws_user_factory, aws_account_id).run()
