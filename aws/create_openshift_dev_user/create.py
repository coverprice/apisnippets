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
import json
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'libs', 'python'))
import dpp.aws
import dpp.google
import dpp.mail

AWS_ACCOUNT_PROFILE_NAME = "openshift-dev"
SPREADSHEET_ID = '1TxlsWyV970ct9EYaPrnSU5Ag7eTKw3Yfi2zfLsfqgxM'
# The following spreadsheet is a copy of the original, used for testing.
# SPREADSHEET_ID = '1SQtqxKN6GU-zjXOYlPbrDUUrnQmRKBmVu-7vuDvS2g8'

REFRESH_TOKEN_FILE = os.path.expanduser('~/.secrets/gcp_service_accounts/refresh_token.txt')

# Despite the '_SECRET' name, this is not actually a secret and it's fine to bake this to source code. This
# 'secret' doesn't actually grant any abilities by itself. The first time a user runs this script, this
# data is used to identify the app and generate a URL that the script user must copy/paste into a
# browser, which will tell the user who is doing the requesting (OpenShift DPP bot) and what they
# want to access (the 'send message' ability of the user's Gmail). It's up to the user to approve that,
# which will ultimately result in an ephemeral access/refresh token that the script can use, and *those*
# are kept secret.
GMAIL_CLIENT_SECRET = """
{
  "installed": {
    "client_id": "969537810335-lk3q1l1c4ftpp8d03a98lstmfrvbnd1h.apps.googleusercontent.com",
    "project_id": "openshift-devproducti",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://www.googleapis.com/oauth2/v3/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "_xDcGtTYOeiKRBzyXtLpk2dT",
    "redirect_uris": [
      "urn:ietf:wg:oauth:2.0:oob",
      "http://localhost"
    ]
  }
}
"""


def get_parser():
    parser = argparse.ArgumentParser(description='Creates an AWS user account in the {} account'.format(AWS_ACCOUNT_PROFILE_NAME))
    parser.add_argument('--dry-run', action='store_true',
        help="Perform all actions but don't create the AWS account or update the spreadsheet.")
    parser.add_argument('--debug', action='store_true',
        help="Print debugging messages.")

    subparsers = parser.add_subparsers(title="commands", dest="command")

    # The "spreadsheet" sub-command
    from_spreadsheet = subparsers.add_parser('spreadsheet')
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
    )

    workflow.run([user])
    if user.status != create_user.UserCreateStatus.ACCOUNT_CREATED:
        return

    output_string = user.output_message.as_string()
    if args.outfile is None:
        sys.stdout.write(output_string)
    else:
        if not args.dry_run:
            with open(args.outfile, 'w') as fh:
                fh.write(output_string),


def spreadsheet_workflow(args, workflow):
    if not os.path.isfile(args.gcp_credentials_file):
        print("Fatal error: GCP credentials file '{}' is not a file.".format(args.gcp_credentials_file), file=sys.stderr)
        sys.exit(1)

    spreadsheet_data_bridge = create_user.GoogleSheetsDataBridge(
        spreadsheet_id=SPREADSHEET_ID,
        service_account_file=args.gcp_credentials_file,
    )
    # Note: we instantiate the email service *before* we call workflow.run(), so that if the
    # script user needs to authenticate with the Gmail API, they are prompted here and not *after*
    # accounts have been created. This avoids a situation where the user messes up their
    # Gmail authentication, leaving the script in a state where accounts have been provisioned
    # but there's no way to send the credentials.
    gmail_service = dpp.google.get_gmail_service(
        client_config=json.loads(GMAIL_CLIENT_SECRET),
        refresh_token_file=REFRESH_TOKEN_FILE,
    )

    if not args.dry_run:
        spreadsheet_data_bridge.fix_up_user_status()
    users_to_create = spreadsheet_data_bridge.get_users_to_create()

    if not len(users_to_create):
        print("No users to create.")
        sys.exit(0)

    if args.dry_run:
        # This causes emails to be send to the script runner user, not the user_to_create.
        email_sender = dpp.google.FakeEmailSender(service=gmail_service)
        if args.debug:
            email_sender.send_to_self(enabled=True)
            email_sender.output_body(enabled=True)
    else:
        email_sender = dpp.google.EmailSender(service=gmail_service)

    workflow.run(users_to_create)

    print("Emailing users with credentials...")
    for user in users_to_create:
        if user.status == create_user.UserCreateStatus.ACCOUNT_CREATED:
            email_sender.send(user.output_message)

    if not args.dry_run:
        spreadsheet_data_bridge.update_user_status(users_to_create)


def setup_logging(enable_debug=False):
    """
    If we naively enable logging.DEBUG for the root logger, we'll get debug messages
    for *all* Python modules, even 3rd-party ones. This is typically too verbose,
    so this function restricts it to just modules under our direct control.
    """
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
        'dpp.ldap.LdapSession',
        'dpp.google.gmail.send',
    ]
    for module in modules_to_debug:
        mod_logger = logging.getLogger(module)
        mod_logger.setLevel(level)
        mod_logger.addHandler(handler)


def get_workflow(args):
    aws_session = dpp.aws.AwsSession.for_profile(profile_name=AWS_ACCOUNT_PROFILE_NAME)
    aws_account_id = aws_session.get_account_id()
    iam_operations = dpp.aws.IamOperations.for_session(aws_session=aws_session)
    if args.dry_run:
        aws_user_factory = dpp.aws.FakeUserFactory()
    else:
        aws_user_factory = dpp.aws.UserFactory(iam_operations)

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
    print("Done")

main()
