#!/usr/bin/env python3

"""
ldap3 is a Python3 LDAP API. Install with:

$ pip-3 install --upgrade ldap3
"""
import ldap3
import logging
logger = logging.getLogger(__name__)
from pprint import pprint

# To get a list of all attributes, connect to the VPN and run something like this:
# $ ldapsearch -x -H ldap://ldap.corp.redhat.com -L -b 'dc=redhat,dc=com' 'uid=jrussell'

class LdapSession(object):
    def __init__(self):
        # Requires VPN connection to work.
        ldap_host = 'ldap.corp.redhat.com'
        logger.debug('Connecting to LDAP server: {}'.format(ldap_host))
        self.conn = ldap3.Connection(ldap_host, auto_bind=True)

    def search(self, search_filter, search_base, return_attributes=None):
        if return_attributes is None:
            return_attributes = ldap3.ALL_ATTRIBUTES

        found = self.conn.search(
            search_base=search_base,
            search_filter=search_filter,
            attributes=return_attributes,
        )
        if not found:
            return None
        return [entry for entry in self.conn.entries]
