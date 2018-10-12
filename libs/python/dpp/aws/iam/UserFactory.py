#!/bin/env python3

from pprint import pprint
from .generate_password import generate_password
from .IamOperations import IamOperations


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
        password = self._generate_password()
        user = self._create_user_record(username=username)
        self._attach_user_to_groups(user, group_names)
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


    def _generate_password(self):
        policy = self.iam_ops.get_password_policy()
        return generate_password(
            min_length=min(12, policy.minimum_password_length),
            use_lowercase=policy.require_lowercase_characters,
            use_uppercase=policy.require_uppercase_characters,
            use_digits=policy.require_numbers,
            use_symbols=policy.require_symbols,
        )


class FakeUserFactory(object):
    """Replaces AWS UserFactory for use in tests"""
    def create_user(self, username, group_names=[]):
        return {
            'username': username,
            'password': 'some_password',
            'access_key_id': 'some_access_key_id',
            'secret_access_key': 'some_secret_access_key',
        }
