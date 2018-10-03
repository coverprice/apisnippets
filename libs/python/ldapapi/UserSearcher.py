#!/usr/bin/env python3

import ldap3
import re
from pprint import pprint
from .LdapSession import LdapSession
from .UserRecord import UserRecord


class UserSearcher(object):
    def __init__(self, session=None):
        if session is None:
            session = LdapSession()
        self.session = session


    def find_by_uid(self, uid, search_deleted_users=False):
        """
        @return UserRecord | None
        """
        response = self.session.search(
            search_filter='(uid={})'.format(uid),
            search_deleted_users=search_deleted_users,
        )
        if response is None:
            return None
        return UserRecord.from_ldap_entry(response[0])


    def find_by_email(self, email, search_deleted_users=False):
        """
        @return UserRecord | None
        """
        email = email.lower().strip()
        if not email.endswith('@redhat.com'):
            raise Exception('Email does not have a @redhat.com domain: {}'.format(email))

        if '=' in email or ' ' in email:
            raise Exception("Email contains forbidden characters: '{}'".format(email))

        for attr in ['mail', 'rhatPreferredAlias', 'rhatPrimaryMail']:
            # It's possible to put all these into a single search criteria, but this is MUCH SLOWER.
            response = self.session.search(
                search_filter='({attr}={email})'.format(attr=attr, email=email),
                search_deleted_users=search_deleted_users,
            )
            if response is not None:
                return UserRecord.from_ldap_entry(response[0])
        return None
