#!/bin/env python3

"""
This script uses the AWS APIs to list all AWS accounts in the organization, and all IAM accounts (users) in each account.
It generates a CSV to stdout.

It relies on a "coreosinc" profile being available in ~/.aws/credentials, which should map to the Master Account (aka Root Account).
"""

import sys
import csv
from pprint import pprint
from awsapi.utils import (get_session, get_sts_client, get_sts_token_for_account, get_accounts)
from awsapi.IamOperations import IamOperations

# Important: In AWS, "account" refers to a resource container (VMs, networks, etc), and "IAM account" refers to (typically) a person.
# "IAM accounts" (also referred to as "users") are contained within "accounts".
# To avoid users having to create a new IAM account in every account they need access to, the IAM accounts tend to be centralized
# into a single account, and then AWS Roles are set up that allow each IAM account to "Assume Role" in other accounts. I.e. the user
# will log into their IAM account, then "Assume Role" to switch into a specific role in another account to perform some operation.

# AWS Root Account ID - This is the master account. Sub-accounts are organized in a hierarchy using AWS Organizations.
ROOT_ACCOUNT_ID = '595879546273'

session = get_session(profile_name="coreosinc")
sts_client = get_sts_client(session)
accounts = get_accounts(session)
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
    'Account Arn',
    'User Name',
    'User Id',
    'User Arn',
    'Password Last Used',
])

for account in active_accounts:
    if account['Id'] == ROOT_ACCOUNT_ID:
        iam_ops = IamOperations.for_session(session)
    else:
        sts_token = get_sts_token_for_account(sts_client, ROOT_ACCOUNT_ID, account['Id'])
        if sts_token is None:
            raise Exception("Could not get STS token for {}".format(account['Name']))
        iam_ops = IamOperations.for_account(sts_token['Credentials'])

    iam_account_alias = iam_ops.get_account_alias()
    if iam_account_alias is None:
        iam_account_alias = '[None]'
    iam_accounts = iam_ops.get_user_accounts()

    if len(iam_accounts) == 0:
        iam_accounts = [
            {
                'Arn': '[No users]',
                'UserId': '[No users]',
                'UserName': '[No users]',
                'PasswordLastUsed': None,
            }
        ]

    for iam_account in iam_accounts:
        try:
            password_last_used = iam_account['PasswordLastUsed'].strftime('%Y-%m-%d')
        except (KeyError, AttributeError):
            password_last_used = None
        csvout.writerow([
            account['Name'],
            iam_account_alias,
            account['Id'],
            account['Arn'],
            iam_account['UserName'],
            iam_account['UserId'],
            iam_account['Arn'],
            password_last_used,
        ])
