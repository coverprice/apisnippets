#!/bin/env python3
import boto3
import botocore
import sys
import functools
import secrets
from pprint import pprint
from .AwsSession import AwsSession


class IamOperations(object):
    """
    Class for making various IAM operations easier
    """
    def __init__(self, session, iam_client):
        self.session = session
        self.iam_client = iam_client


    @staticmethod
    def for_session(session):
        """
        Use this factory method when you have a session that's already tied to the account you want the IAM client for
        """
        iam_client = session.client('iam')
        return IamOperations(session=session, iam_client=iam_client)


    @staticmethod
    def for_account(session, credentials):
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
        return IamOperations(session=session, iam_client=iam_client)


    @functools.lru_cache()
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


    @functools.lru_cache()
    def get_all_policies(self):
        policy_paginator = self.iam_client.get_paginator('list_policies')
        ret = []
        for response in policy_paginator.paginate(Scope='All', OnlyAttached=False):
            ret += response['Policies']
        return ret


    @functools.lru_cache()
    def get_policy(self, policy_arn : str):
        response = self.iam_client.get_policy(PolicyArn=policy_arn)
        return response['Policy']


    @functools.lru_cache()
    def get_policy_version(self, policy_arn : str, version : str):
        response = self.iam_client.get_policy_version(PolicyArn=policy_arn, VersionId=version)
        return response['PolicyVersion']


    @functools.lru_cache()
    def get_all_groups(self):
        group_paginator = self.iam_client.get_paginator('list_groups')
        ret = []
        for response in group_paginator.paginate():
            ret += response['Groups']
        return ret


    def get_user(self, username : str):
        """
        @param username
        @return IAM.User
        """
        iam_resource = self.session.resource('iam')
        user = iam_resource.User(username)
        return user


    def user_exists(self, user):
        """
        @param user IAM.User (obtained first with get_user)
        @return boolean - True if the user exists
        """
        try:
            user.load()
            return True
        except self.iam_client.exceptions.NoSuchEntityException:
            return False


    @functools.lru_cache()
    def get_password_policy(self):
        iam_resource = self.session.resource('iam')
        account_password_policy = iam_resource.AccountPasswordPolicy()
        account_password_policy.load()
        return account_password_policy


class RecordExistsException(Exception):
    pass  


class UserFactory(object):
    """
    Class that encapsulates the job of creating a new AWS user
    """
    def __init__(self, iam_ops : IamOperations):
        self.iam_ops = iam_ops


    def create_user(self, username : str, group_names : list):
        """
        @param username - username to create
        @param group_names - list of policy names to attach
        """
        user = self._create_user_record(username=username)

        self._attach_user_to_groups(user, group_names)

        password = self._generate_new_password()
        user.create_login_profile(Password=password, PasswordResetRequired=True)

        access_key_pair = user.create_access_key_pair()

        return {
            'username': user.user_name,
            'password': password,
            'access_key_id': access_key_pair.id,
            'secret_access_key': access_key_pair.secret,
        }


    def _create_user_record(self, username : str):
        """
        @return IAM.User
        """
        user = self.iam_ops.get_user(username=username)

        if self.iam_ops.user_exists(user):
            raise RecordExistsException("Username {} already exists".format(username))

        user.create()
        return user


    def _attach_user_to_policies(self, user, policy_names : list):
        if len(policy_names) == 0:
            return
        policy_names = list(set(policy_names))      # Make unique
        for policy in self.iam_ops.get_all_policies():
            if policy['PolicyName'] in policy_names:
                user.attach_policy(PolicyArn=policy['PolicyArn'])


    def _attach_user_to_groups(self, user, group_names : list):
        if len(group_names) == 0:
            return
        group_names = list(set(group_names))       # Make unique
        for group in self.iam_ops.get_all_groups():
            if group['GroupName'] in group_names:
                user.add_group(GroupName=group['GroupName'])


    def _generate_new_password(self):
        def all_chars_in_range(lo, hi):
            return [chr(x) for x in range(ord(lo), ord(hi)+1)]

        policy = self.iam_ops.get_password_policy()
        chars = []
        if policy.require_lowercase_characters:
            chars += all_chars_in_range('a', 'z')
        if policy.require_uppercase_characters:
            chars += all_chars_in_range('A', 'Z')
        if policy.require_numbers:
            chars += all_chars_in_range('0', '9')
        if policy.require_symbols:
            chars += list(r"!@#$%^&*()_+-=[]{}|'")     # This list was copied from AWS's UI

        if len(chars) == 0:
            raise Exception("Password policy gives us no password characters to choose from!")

        new_password = ''
        password_len = min(12, policy.minimum_password_length)
        for _ in range(0, password_len):
            new_password += secrets.choice(chars)        # This is cryptographically-safe
        return new_password
