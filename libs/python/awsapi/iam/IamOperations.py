#!/bin/env python3

"""
boto3 & botocore are the AWS python API libraries. They can be installed with:

$ sudo dnf install python3-boto3 python3-botocore
"""

import boto3
import botocore
import functools
from pprint import pprint
from ..AwsSession import AwsSession
from ..Operations import Operations


class IamOperations(Operations):
    @classmethod
    def get_service_client_name(cls):
        return 'iam'


    @functools.lru_cache()
    def get_account_alias(self):
        try:
            response = self.aws_client.list_account_aliases()
        except botocore.exceptions.ClientError:
            return '[Permission denied]'
        if len(response['AccountAliases']) == 0:
            return None
        return response['AccountAliases'][0]


    def get_IAM_accounts(self):
        """
        Return a list of all the IAM accounts within that account. Each list item looks like this:
	(copied from https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/iam.html#IAM.Client.list_users)
	    {
		'Path': 'string',
		'UserName': 'string',
		'UserId': 'string',
		'Arn': 'string',
		'CreateDate': datetime(2015, 1, 1),
		'PasswordLastUsed': datetime(2015, 1, 1),
		'PermissionsBoundary': {
		    'PermissionsBoundaryType': 'PermissionsBoundaryPolicy',
		    'PermissionsBoundaryArn': 'string'
		}
	    }
        """
        user_paginator = self.aws_client.get_paginator('list_users')
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
        policy_paginator = self.aws_client.get_paginator('list_policies')
        ret = []
        for response in policy_paginator.paginate(Scope='All', OnlyAttached=False):
            ret += response['Policies']
        return ret


    @functools.lru_cache()
    def get_policy(self, policy_arn : str):
        response = self.aws_client.get_policy(PolicyArn=policy_arn)
        return response['Policy']


    @functools.lru_cache()
    def get_policy_version(self, policy_arn : str, version : str):
        response = self.aws_client.get_policy_version(PolicyArn=policy_arn, VersionId=version)
        return response['PolicyVersion']


    @functools.lru_cache()
    def get_all_groups(self):
        group_paginator = self.aws_client.get_paginator('list_groups')
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
        except self.aws_client.exceptions.NoSuchEntityException:
            return False


    @functools.lru_cache()
    def get_password_policy(self):
        iam_resource = self.session.resource('iam')
        account_password_policy = iam_resource.AccountPasswordPolicy()
        account_password_policy.load()
        return account_password_policy
