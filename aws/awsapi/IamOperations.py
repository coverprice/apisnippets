#!/bin/env python3
import boto3
import botocore
import sys
from pprint import pprint


class IamOperations(object):
    """
    Class for making various IAM operations easier
    """
    def __init__(self, iam_client):
        self.iam_client = iam_client


    @staticmethod
    def for_session(session):
        """
        Use this factory method when you have a session that's already tied to the account you want the IAM client for
        """
        iam_client = session.client('iam')
        return IamOperations(iam_client=iam_client)


    @staticmethod
    def for_account(credentials):
        """
        Use this factory method when you have a session tied to an AWS account, but you want an IAM client for a different account.

        Given the ephemeral credentials (which also imply a specific sub-account),
        and return an IAM (Identity Access Management) client for that sub-account with those credentials.
        """
        iam_client = boto3.client(
            service_name='iam',
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken'],
        )
        return IamOperations(iam_client=iam_client)


    def get_account_alias(self):
        try:
            response = self.iam_client.list_account_aliases()
        except botocore.exceptions.ClientError:
            return '[Permission denied]'
        if len(response['AccountAliases']) == 0:
            return None
        return response['AccountAliases'][0]


    def get_user_accounts(self):
        """
        Given an IAM client and metadata about a specific account (a dict from get_accounts()),
        get a list of all the IAM accounts within that account.
        """
        user_paginator = self.iam_client.get_paginator('list_users')
        ret = []
        try:
            for response in user_paginator.paginate():
                ret += response['Users']
        except botocore.exceptions.ClientError:
            return [
                {
                    'Arn': '[Permission Denied]',
                    'UserId': '[Permission Denied]',
                    'UserName': '[Permission Denied]',
                    'PasswordLastUsed': None,
                }
            ]
        ret = sorted(ret, key=lambda rec:str.lower(rec['UserName']))
        return ret


    def get_all_policies(self):
        policy_paginator = self.iam_client.get_paginator('list_policies')
        ret = []
        for response in policy_paginator.paginate(Scope='Local', OnlyAttached=False):
            ret += response['Policies']
        return ret


    def get_policy(self, policy_arn):
        response = self.iam_client.get_policy(PolicyArn=policy_arn)
        return response['Policy']


    def get_policy_version(self, policy_arn, version):
        response = self.iam_client.get_policy_version(PolicyArn=policy_arn, VersionId=version)
        return response['PolicyVersion']
