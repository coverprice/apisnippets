#!/bin/env python3

"""
This script uses the AWS APIs to list all AWS accounts in the organization, and all IAM accounts (users) in each account.
It generates a CSV to stdout.

It relies on a "coreosinc" profile being available in ~/.aws/credentials, which should map to the Master Account (aka Root Account).
"""

import sys
import csv
from pprint import pprint
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'libs/python'))
import awsapi

# Important: In AWS, "account" refers to a resource container (VMs, networks, etc), and "IAM account" refers to (typically) a person.
# "IAM accounts" (also referred to as "users") are contained within "accounts".
# To avoid users having to create a new IAM account in every account they need access to, the IAM accounts tend to be centralized
# into a single account, and then AWS Roles are set up that allow each IAM account to "Assume Role" in other accounts. I.e. the user
# will log into their IAM account, then "Assume Role" to switch into a specific role in another account to perform some operation.

# AWS Root Account ID - This is the master account. Sub-accounts are organized in a hierarchy using AWS Organizations.
ROOT_ACCOUNT_ID = '595879546273'

aws_session = awsapi.AwsSession.for_profile(profile_name="coreosinc")
accounts = aws_session.get_accounts()
active_accounts = [ acct for acct in accounts if acct['Status'] == 'ACTIVE' ]

csvout = csv.writer(
    sys.stdout,
    delimiter=',',
    quotechar='|',
    quoting=csv.QUOTE_MINIMAL,
)
csvout.writerow([
    'Account Name',
    'Account Alias',
    'Account Id',
    'Instance Name',
    'Keypair Name',
    'Location',
    'Launch Time',
    'State',
])

for account in active_accounts:
    if account['Id'] == ROOT_ACCOUNT_ID:
        iam_ops = awsapi.IamOperations.for_session(aws_session=aws_session)
        ec2_ops = awsapi.Ec2Operations.for_session(aws_session=aws_session)
    else:
        sts_token = aws_session.get_sts_token_for_account(ROOT_ACCOUNT_ID, account['Id'])
        if sts_token is None:
            raise Exception("Could not get STS token for {}".format(account['Name']))
        iam_ops = awsapi.IamOperations.for_account(aws_session=aws_session, credentials=sts_token['Credentials'])
        ec2_ops = awsapi.Ec2Operations.for_account(aws_session=aws_session, credentials=sts_token['Credentials'])

    iam_account_alias = iam_ops.get_account_alias()
    if iam_account_alias is None:
        iam_account_alias = '[None]'

    # for region in ec2_ops.list_regions():
    reservations = ec2_ops.list_instances()
    for reservation in reservations:
        # pprint(reservation)
        # sys.exit()
        for instance in reservation['Instances']:
            csvout.writerow([
                account['Name'],
                iam_account_alias,
                account['Id'],
                instance['InstanceId'],
                instance['KeyName'],
                instance['Placement']['AvailabilityZone'],
                str(instance['LaunchTime']),
                instance['State']['Name'],
            ])
