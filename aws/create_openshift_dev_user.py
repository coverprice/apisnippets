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

ACCOUNT_NAME = "openshift-dev"
TEMPLATE = """
AWS account: {alias} ({account_id})
URL: https://{alias}.signin.aws.amazon.com/console

Username: {username}
Initial password: {password}

Copy the following to your ~/.aws/credentials file:

[{alias}]
aws_access_key_id = {access_key_id}
aws_secret_access_key = {secret_access_key}
"""

def parse_args():
    parser = argparse.ArgumentParser(description='Creates an AWS user account in the {} account'.format(ACCOUNT_NAME))
    parser.add_argument('username', action="store")
    return parser.parse_args()


def get_user_factory(aws_session):
    iam_ops = awsapi.IamOperations.for_session(aws_session.session)
    user_factory = awsapi.UserFactory(iam_ops)
    return user_factory


def create_user(result, aws_account_id, account_alias):
    global TEMPLATE
    new_user = TEMPLATE.format(
        alias=account_alias,
        account_id=aws_account_id,
        username=result['username'],
        password=result['password'],
        access_key_id=result['access_key_id'],
        secret_access_key=result['secret_access_key'],
    )
    print(new_user)

args = parse_args()
username = args.username
aws_session = awsapi.AwsSession.for_profile(profile_name=ACCOUNT_NAME)
result = get_user_factory(aws_session).create_user(username=username, group_names=["Dev"])
create_user(
    result,
    aws_session.get_account_id(),
    account_alias=ACCOUNT_NAME,
)
