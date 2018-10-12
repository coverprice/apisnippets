#!/bin/env python3

"""
This script uses the AWS APIs to export all AWS access policies and roles in the core-services AWS account.
It generates JSON files for each access policy, and role.

It relies on a "coreosinc" profile being available in ~/.aws/credentials, which should map to the Master Account (aka Root Account).
"""

import sys
import csv
from pprint import pprint
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'libs', 'python'))
import dpp.aws

# Important: In AWS, "account" refers to a resource container (VMs, networks, etc), and "IAM account" refers to (typically) a person.
# "IAM accounts" (also referred to as "users") are contained within "accounts".
# To avoid users having to create a new IAM account in every account they need access to, the IAM accounts tend to be centralized
# into a single account, and then AWS Roles are set up that allow each IAM account to "Assume Role" in other accounts. I.e. the user
# will log into their IAM account, then "Assume Role" to switch into a specific role in another account to perform some operation.

# AWS Root Account ID - This is the master account. Sub-accounts are organized in a hierarchy using AWS Organizations.
ROOT_ACCOUNT_ID = '595879546273'
CORE_SERVICES_ACCOUNT_ID = '816138690521'

# Program begins here
aws_session = dpp.aws.AwsSession.for_profile(profile_name="coreosinc")
sts_token = aws_session.get_sts_token_for_account(ROOT_ACCOUNT_ID, CORE_SERVICES_ACCOUNT_ID)
iam_ops = dpp.aws.IamOperations.for_account(aws_session.session, sts_token['Credentials'])
policies = iam_ops.get_all_policies()
for policy_metadata in policies:
    policy = iam_ops.get_policy(policy_metadata['Arn'])
    policy_version = iam_ops.get_policy_version(policy_metadata['Arn'], policy_metadata['DefaultVersionId'])
    pprint(policy_version)

sys.exit(1)
