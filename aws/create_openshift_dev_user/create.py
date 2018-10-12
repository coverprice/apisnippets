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
import logging
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'libs', 'python'))
import awsapi

AWS_ACCOUNT_PROFILE_NAME = "openshift-dev"
SPREADSHEET_ID = '1TxlsWyV970ct9EYaPrnSU5Ag7eTKw3Yfi2zfLsfqgxM'
# The following spreadsheet is a copy of the original, used for testing.
# SPREADSHEET_ID = '1SQtqxKN6GU-zjXOYlPbrDUUrnQmRKBmVu-7vuDvS2g8'

def get_parser():
    parser = argparse.ArgumentParser(description='Creates an AWS user account in the {} account'.format(AWS_ACCOUNT_PROFILE_NAME))
    parser.add_argument('--dry-run', action='store_true',
        help="Perform all actions but don't create the AWS account or update the spreadsheet.")
    parser.add_argument('--debug', action='store_true',
        help="Print debugging messages.")

    subparsers = parser.add_subparsers(title="commands", dest="command")

    # The "spreadsheet" sub-command
    from_spreadsheet = subparsers.add_parser('spreadsheet')
    from_spreadsheet.add_argument('-o', '--outdir', nargs='?', type=str, default=None,
        help='Output directory to write credentials to.')
    from_spreadsheet.add_argument('--gcp-credentials-file', nargs='?', type=str,
        default=os.path.expanduser('~/.secrets/gcp_service_accounts/openshift-devproductivity-bot.json'),
        help="Path to Google Service Account credentials file")

    # The "user" sub-command
    from_userid = subparsers.add_parser('user')
    from_userid.add_argument('username', action="store",
        help='Kerberos ID or email address of the user to add')
    from_userid.add_argument('-k', '--keyfile', nargs='?', type=argparse.FileType('r'), default=None,
        help='When a user is specified, this is the GPG key file to import and encrypt with. (If not specified, output is unencrypted')
    from_userid.add_argument('-o', '--outfile', nargs='?', type=str, default=None,
        help='Output filename (default: stdout)')

    return parser


def cli_workflow(args, workflow):
    # get user from cli args(args)
    gpg_key = None
    if args.keyfile is not None:
        gpg_key = args.keyfile.read()


    user = create_user.UserToCreate(
        user_id=args.username,
        gpg_key=gpg_key,
        output_file=output_file,
    )

    workflow.run([user])
    if user.status != create_user.UserCreateStatus.ACCOUNT_CREATED:
        return

    if args.outfile is None:
        sys.stdout.write("{email}\n{message}\n\n".format(
            email=user.email,
            message=user.output_message,
        ))
    else:
        if not args.dry_run:
            with open(args.outfile, 'w') as fh:
                fh.write(user.output_message)


def spreadsheet_workflow(args, workflow):
    outdir = args.outdir
    if not outdir:
        outdir = os.getcwd()
    if not os.path.isdir(outdir):
        print("Fatal error: Output dir '{}' is not a directory.".format(outdir), file=sys.stderr)
        sys.exit(1)

    if not os.path.isfile(args.gcp_credentials_file):
        print("Fatal error: GCP credentials file '{}' is not a file.".format(args.gcp_credentials_file), file=sys.stderr)
        sys.exit(1)

    spreadsheet_data_bridge = create_user.GoogleSheetsDataBridge(
        spreadsheet_id=SPREADSHEET_ID,
        service_account_file=args.gcp_credentials_file,
    )
    if not args.dry_run:
        spreadsheet_data_bridge.fix_up_user_status()
    users_to_create = spreadsheet_data_bridge.get_users_to_create()

    workflow.run(users_to_create)

    if not args.dry_run:
        for user in users_to_create:
            if user.status == create_user.UserCreateStatus.ACCOUNT_CREATED:
                output_file = os.path.join(outdir, '{}.gpg'.format(user.email))
                with open(output_file, 'w') as fh:
                    fh.write(user.output_message)

        spreadsheet_data_bridge.update_user_status(users_to_create)


def setup_logging(enable_debug=False):
    logging.basicConfig(handlers=[logging.NullHandler()])

    level = logging.INFO
    if enable_debug:
        level = logging.DEBUG

    formatter = logging.Formatter(fmt='%(levelname)-8s: %(message)s')

    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(formatter)

    modules_to_debug = [
        'create_user',
        'ldapapi.LdapSession',
    ]
    for module in modules_to_debug:
        mod_logger = logging.getLogger(module)
        mod_logger.setLevel(level)
        mod_logger.addHandler(handler)


def get_workflow(args):
    aws_session = awsapi.AwsSession.for_profile(profile_name=AWS_ACCOUNT_PROFILE_NAME)
    aws_account_id = aws_session.get_account_id()
    iam_operations = awsapi.IamOperations.for_session(aws_session=aws_session)
    if args.dry_run:
        aws_user_factory = awsapi.FakeUserFactory()
    else:
        aws_user_factory = awsapi.UserFactory(iam_operations)

    return create_user.CreateUserWorkflow(
        aws_user_factory=aws_user_factory,
        iam_operations=iam_operations,
        aws_account_id=aws_account_id,
        aws_account_alias=AWS_ACCOUNT_PROFILE_NAME,
    )


def main():
    parser = get_parser()
    args = parser.parse_args()

    setup_logging(args.debug)
    workflow = get_workflow(args)

    if args.command == 'spreadsheet':
        spreadsheet_workflow(args, workflow)
    elif args.command == 'user':
        cli_workflow(args, workflow)
    else:
        parser.print_usage()
        sys.exit(1)

main()
