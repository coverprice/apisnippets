#!/usr/bin/env python3

import ldap3
import sys

# To get a list of all attributes, connect to the VPN and run something like this:
# $ ldapsearch -x -H ldap://ldap.corp.redhat.com -L -b 'dc=redhat,dc=com' 'uid=jrussell'

# Requires VPN connection to work.
LDAP_CONN = ldap3.Connection('ldap.corp.redhat.com', auto_bind=True)

def display_ldap_entry(entry):
    # print("{} {} {} {}".format(str(entry['uid']), str(entry['mail']), str(entry['cn']), str(entry['rhatJobTitle'])))
    print("{} {} {} {}".format(str(entry['uid']), str(entry['mail']), str(entry['cn']), ''))


def ldap_find_user_by_uid(uid, search_deleted_users=False):
    global LDAP_CONN
    domain = ['dc=redhat', 'dc=com']
    if search_deleted_users:
        domain.append('ou=DeletedUsers')

    found = LDAP_CONN.search(
        ','.join(domain),
        '(uid={})'.format(uid),
        attributes=['uid', 'cn','mail', 'rhatJobTitle'],
    )
    if not found:
        return None
    return [entry for entry in LDAP_CONN.entries]


def find_user_by_uid(uid):
    result = ldap_find_user_by_uid(uid, search_deleted_users=False)
    is_deleted = False
    if result is None:
        result = ldap_find_user_by_uid(uid, search_deleted_users=True)
        is_deleted = True

    if result is None:
        print("{0}   Not found".format(uid))
    elif len(result) > 1:
        print("Multiple found")
        for entry in result:
            display_ldap_entry(entry)
    else:
        print("{0} FOUND".format(uid))
        if is_deleted:
            print("*** USER IS NO LONGER AN EMPLOYEE ***")
        display_ldap_entry(result[0])

result = find_user_by_uid('jrussell')
