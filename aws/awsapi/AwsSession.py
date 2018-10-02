#!/bin/env python3
import boto3
import botocore
import functools
from pprint import pprint


class AwsSession(object):
    def __init__(self, boto3session):
        self.session = boto3session

    @staticmethod
    def for_profile(profile_name):
        """
        Return an AWS API session, using the ~/.aws/credentials "profile" name
        """
        return AwsSession(boto3.session.Session(profile_name=profile_name))

    @functools.lru_cache()
    def get_sts_client(self):
        """
        Return a STS (Security Token Service) API client
        """
        return self.session.client('sts')

    @functools.lru_cache()
    def get_account_id(self) -> str:
        """
        @return str - the 12 digit AWS account ID
        """
        response = self.get_sts_client().get_caller_identity()
        return response['Account']

    def get_accounts(self):
        """
        Return a list of dicts, each item is metadata about an account within the organization.
        """
        org_client = self.session.client('organizations')
        account_paginator = org_client.get_paginator('list_accounts')
        account_iterator = account_paginator.paginate()

        ret = []
        for response in account_iterator:
            ret += response['Accounts']
        ret = sorted(ret, key=lambda rec:str.lower(rec['Name']))
        return ret

    def get_sts_token_for_account(self, root_account_id, assume_account_id):
        """
        Use the STS (Security Token Service) client to obtain ephemeral credentials that will allow the caller to
        temporarily assume the OrganizationAccountAccessRole role in a sub-account.
        (This Role was automatically set up when the account was created under the Root account.)

        @param root_account_id string - the Account ID (12 digit #) of the AWS Organizations root account
        @param assume_account_id string - the Account ID (12 digit #) of the AWS Organizations account to get a token for
        """
        response = self.get_sts_client().assume_role(
            RoleArn='arn:aws:iam::{}:role/OrganizationAccountAccessRole'.format(assume_account_id),
            RoleSessionName='jrussell_{}_{}'.format(root_account_id, assume_account_id),
            DurationSeconds=1000,
        )
        return response
