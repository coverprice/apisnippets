#!/usr/bin/env python3

"""
ldap3 is a Python3 LDAP API. Install with:

$ pip-3 install --upgrade ldap3
"""
import ldap3
from pprint import pprint

# To get a list of all attributes, connect to the VPN and run something like this:
# $ ldapsearch -x -H ldap://ldap.corp.redhat.com -L -b 'dc=redhat,dc=com' 'uid=jrussell'

class LdapSession(object):
    def __init__(self):
        # Requires VPN connection to work.
        self.conn = ldap3.Connection('ldap.corp.redhat.com', auto_bind=True)

    def search(self, search_filter, return_attributes=None, search_deleted_users=False):
        domain = ['dc=redhat', 'dc=com']
        if search_deleted_users:
            domain.append('ou=DeletedUsers')

        if return_attributes is None:
            return_attributes = ldap3.ALL_ATTRIBUTES

        found = self.conn.search(
            search_base=','.join(domain),
            search_filter=search_filter,
            attributes=return_attributes,
        )
        if not found:
            return None
        return [entry for entry in self.conn.entries]
