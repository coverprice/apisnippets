#!/usr/bin/env python3

import ldap3
import re
from pprint import pprint
from .LdapSession import LdapSession
from .UserRecord import UserRecord


class UserSearcher(object):
    def __init__(self, session=None):
        """
        @raise ConnectionFailure if the LDAP server can't be connected to.
        """
        if session is None:
            session = LdapSession()
        self.session = session

    def _get_search_base(self, search_deleted_users=False):
        domain = ['dc=redhat', 'dc=com']
        if search_deleted_users:
            domain.append('ou=DeletedUsers')
        return ','.join(domain)

    def find_by_uid(self, uid, search_deleted_users=False):
        """
        @return UserRecord | None
        """
        response = self.session.search(
            search_filter='(uid={})'.format(uid),
            search_base=self._get_search_base(search_deleted_users),
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
                search_base=self._get_search_base(search_deleted_users),
            )
            if response is not None:
                return UserRecord.from_ldap_entry(response[0])
        return None
