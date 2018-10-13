#!/bin/env python3

"""
This defines the workflow for creating a set of users in AWS.
"""

import sys
from pprint import pprint
import logging
logger = logging.getLogger(__name__)

import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'libs', 'python'))
import dpp.aws
import dpp.ldap
import dpp.gpg
import dpp.mail

from .message import (
    gen_main_message,
    gen_credentials_message,
)
from .UserToCreate import (
    UserToCreate,
    UserCreateStatus,
)


class CreateUserWorkflow(object):
    def __init__(self,
            ldap_user_searcher : dpp.ldap.UserSearcher,
            aws_user_factory,
            iam_operations : dpp.aws.IamOperations,
            aws_account_id : str,
            aws_account_alias : str,
        ):
        """
        @param ldap_user_searcher:      dpp.ldap.UserSearcher
        @param aws_user_factory:        dpp.aws.UserFactory
        @param iam_operations:          dpp.aws.IamOperations
        @param aws_account_id:          12-digit account ID
        @param aws_account_alias:       alias for the 12-digit account ID (if there is one)
        """
        self.ldap_user_searcher = ldap_user_searcher
        self.aws_user_factory = aws_user_factory
        self.iam_operations = iam_operations
        self.aws_account_id = aws_account_id
        self.aws_account_alias = aws_account_alias


    def run(self, users_to_create : list):
        """

        Runs the workflow. Note that although users are created and each user's email
        message is generated, this object does NOT send the email.

        @param users_to_create [UsersToCreate]
        """
        self._preflight_checks(users_to_create)
        self._decide_go_nogo(users_to_create)
        self._create_users(users_to_create)


    def _preflight_checks(self, users_to_create : list) -> None:
        logger.debug('Getting list of all IAM accounts')
        existing_aws_users = [
            user['UserName'].lower()
            for user in self.iam_operations.get_IAM_accounts()
        ]

        for user in users_to_create:
            self._retrieve_ldap_info(user)

            if user.gpg_key:
                logger.debug('Testing GPG key for user "{}"'.format(user.user_id))
                try:
                    dpp.gpg.encrypt('blah blah blah', user.gpg_key)
                except dpp.gpg.ApiException as e:
                    user.add_error('Failed test encryption on key: ' + str(e))

            if user.kerberos_id is not None and user.kerberos_id in existing_aws_users:
                user.add_error('Account "{}" already exists.'.format(user.kerberos_id))
        
            user.status = UserCreateStatus.FAILED_PREFLIGHT_CHECK if user.has_errors() else UserCreateStatus.READY_TO_CREATE


    def _decide_go_nogo(self, users_to_create):
        """
        Called after pre-flight checks. Looks at the list of users holistically and determines what to do.
        Returns the list of user accounts to create.
        """
        def display_user(user : UserToCreate) -> None:
            print("{email:<22} {kerberos_id:<10}  GPG key: {has_key:<3}  {errors}".format(
                email=user.email,
                kerberos_id=user.kerberos_id,
                has_key='Yes' if user.gpg_key else 'No',
                errors=', '.join(user.errors),
            ))

        if len(users_to_create) == 0:
            print("There are no users to process.")
            sys.exit(0)

        go_users = [user for user in users_to_create if user.status == UserCreateStatus.READY_TO_CREATE]
        nogo_users = [user for user in users_to_create if user.status == UserCreateStatus.FAILED_PREFLIGHT_CHECK]

        if len(nogo_users):
            print("{} have errors and will be skipped:".format(len(nogo_users)))
            for user in nogo_users:
                display_user(user)
            if len(go_users) == 0:
                return []
            print("")


        print("{} will be created:".format(len(go_users)))
        for user in go_users:
            display_user(user)

        answer = input("Proceed? y/n ")
        if len(answer) == 0 or answer.lower() != 'y':
            sys.exit(0)


    def _create_users(self, users_to_create : list) -> None:
        for user in users_to_create:
            if user.status == UserCreateStatus.READY_TO_CREATE:
                aws_user_info = self._create_user(user)
                user.output_message = self._gen_email(user, aws_user_info)


    def _create_user(self, user : UserToCreate) -> None:
        """
        Calls AWS API to create the user and place them into Groups.

        @return dict - block of info about the created user
        """
        logger.debug('Creating user: {}'.format(user.kerberos_id))
        aws_user_info = self.aws_user_factory.create_user(
            username=user.kerberos_id,
            group_names=["Dev"],
        )
        user.status = UserCreateStatus.ACCOUNT_CREATED
        return aws_user_info


    def _gen_email(self, user, aws_user_info):
        """
        Generates a MIME message to send to the user with information about
        accessing the account. The credentials are encrypted and added as an
        attachment.

        @return email.mime.MIMEMultipart
        """
        main_msg = gen_main_message(aws_account_alias=self.aws_account_alias)
        credentials_msg = gen_credentials_message(
            aws_account_alias=self.aws_account_alias,
            aws_account_id=self.aws_account_id,
            aws_user_info=aws_user_info,
        )
        if user.gpg_key:
            logger.debug('Encrypting credentials message for user: {}'.format(user.kerberos_id))
            credentials_msg = dpp.gpg.encrypt(credentials_msg, user.gpg_key)

        email_builder = dpp.mail.EmailBuilder(
            to=user.email,
            subject="{} AWS IAM account provisioned".format(self.aws_account_alias),
        )
        email_builder.add_html_message(body=main_msg)
        email_builder.add_attachment_from_var(
            contents=credentials_msg,
            filename="{}.{}.credentials.txt.gpg".format(user.email, self.aws_account_alias),
        )
        return email_builder.get_mime_message()


    def _retrieve_ldap_info(self, user : UserToCreate) -> None:
        """
        @param User to create user_param - kerberos ID or email address
        @return the user's kerberos ID
        """
        logger.debug('Retrieving LDAP info for user "{}"'.format(user.user_id))
        is_email = '@' in user.user_id
        if is_email and not user.user_id.endswith('@redhat.com'):
            user.add_error('Email addresses must end with @redhat.com : "{}"'.format(user.user_id))
            return

        if is_email:
            ldap_record = self.ldap_user_searcher.find_by_email(user.user_id)
        else:
            ldap_record = self.ldap_user_searcher.find_by_uid(user.user_id)
        if ldap_record is None:
            user.add_error('Could not find LDAP record for user record "{}"'.format(user.user_id))
            return

        user.kerberos_id = ldap_record.uid.lower()
        user.email = ldap_record.primary_email
