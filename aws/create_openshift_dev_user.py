#!/bin/env python3

"""
This script creates a user in the openshift-dev AWS account. It takes a user (or set of users) and emits
encrypted credentials + login information.

It has 2 modes of operation:
1) 'user' - specify the username or user email, and optionally their GPG key on the command line
2) 'spreadsheet' - Retrieve the username/keys from a specific Google Sheets spreadsheet

Various pre-flight checks are made to ensure success:
- the user will be verified against LDAP.
- a trial GPG encryption (if a key is supplied)
- the account doesn't already exist in AWS
"""

import sys
from pprint import pprint
import create_user
import argparse
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'libs', 'python'))
import awsapi

ACCOUNT_NAME = "openshift-dev"
SPREADSHEET_ID = '1TxlsWyV970ct9EYaPrnSU5Ag7eTKw3Yfi2zfLsfqgxM'
SERVICE_ACCOUNT_FILE = os.path.expanduser('~/.secrets/gcp_service_accounts/openshift-devproducti-3fd6f7ce7d12.json')


def get_parser():
    parser = argparse.ArgumentParser(description='Creates an AWS user account in the {} account'.format(ACCOUNT_NAME))
    parser.add_argument('--skip-account-create', action='store_true',
        help="For debugging. Performs all non-AWS steps, but doesn't actually create the AWS account.")

    subparsers = parser.add_subparsers(title="commands", dest="command")

    # The "spreadsheet" sub-command
    from_spreadsheet = subparsers.add_parser('spreadsheet')
    from_spreadsheet.add_argument('-o', '--outdir', nargs='?', type=str, default=None,
        help='Output directory to write credentials to.')

    # The "user" sub-command
    from_userid = subparsers.add_parser('user')
    from_userid.add_argument('username', action="store",
        help='Kerberos ID or email address of the user to add')
    from_userid.add_argument('-k', '--keyfile', nargs='?', type=argparse.FileType('r'), default=None,
        help='When a user is specified, this is the GPG key file to import and encrypt with. (If not specified, output is unencrypted')
    from_userid.add_argument('-o', '--outfile', nargs='?', type=str, default=None,
        help='Output filename (default: stdout)')

    return parser


def get_user_from_cli_args(args) -> list:
    # This means the CLI params specify a single user to create
    gpg_key = None
    if args.keyfile is not None:
        gpg_key = args.keyfile.read()

    output_file = None
    if args.outfile is not None:
        output_file = args.outfile

    return create_user.UserToCreate(
        user_id=args.username,
        gpg_key=gpg_key,
        output_file=output_file,
    )


def get_users_from_spreadsheet(args):
    spreadsheet_data_bridge = create_user.GoogleSheetsDataBridge(
        spreadsheet_id=SPREADSHEET_ID,
        service_account_file=SERVICE_ACCOUNT_FILE,
    )
    outdir = args.outdir
    if not outdir:
        outdir = os.getcwd()
    if not os.path.isdir(outdir):
        print("Fatal error: Output dir '{}' is not a directory.".format(outdir), file=sys.stderr)
        sys.exit(1)
        
    users_to_create = spreadsheet_data_bridge.get_users()

    for user in users_to_create:
        user.output_file = os.path.join(outdir, '{}.gpg'.format(user.email))

    return users_to_create


def main():
    parser = get_parser()
    args = parser.parse_args()

    aws_session = awsapi.AwsSession.for_profile(profile_name=ACCOUNT_NAME)
    aws_account_id = aws_session.get_account_id()
    iam_operations = awsapi.IamOperations.for_session(aws_session.session)
    if args.skip_account_create:
        aws_user_factory = awsapi.FakeUserFactory()
    else:
        aws_user_factory = awsapi.UserFactory(iam_operations)

    if args.command == 'spreadsheet':
        users_to_create = get_users_from_spreadsheet(args)
    elif args.command == 'user':
        users_to_create = [get_user_from_cli_args(args)]

    else:
        parser.print_usage()
        sys.exit(1)

    workflow = create_user.CreateUserWorkflow(
        aws_user_factory=aws_user_factory,
        iam_operations=iam_operations,
        aws_account_id=aws_account_id,
        aws_account_alias=ACCOUNT_NAME,
    )
    workflow.run(users_to_create)

    # TODO - update the spreadsheet to reflect that the users have been created.
    # TODO - update the spreadsheet with GPG errors?
    # TODO - Inspect GPG metadata and report errors like expired keys / multiple keys?
    # if args.command == 'spreadsheet':
    #    update_spreadsheet(users_to_create)

main()
