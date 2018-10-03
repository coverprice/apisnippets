#!/usr/bin/env python3

import re
from pprint import pprint


class UserRecord(object):
    def __init__(self):
        self.full_name = None
        self.first_name = None
        self.surname = None
        self.uid = None                 # Kerberos ID
        self.uuid = None
        self.github = None
        self.primary_email = None
        self.emails = []                # All email aliases, primary first
        self.is_openshift = False       # Is a member of the OpenShift org?
        self.is_employed = False

    @staticmethod
    def from_ldap_entry(entry, is_employed=True):
        user = UserRecord()
        d = entry.entry_attributes_as_dict

        user.full_name = str(d['cn'][0])
        user.first_name = str(d['displayName'][0])
        user.surname = str(d['sn'][0])
        user.uid = str(d['uid'][0])
        user.uuid = str(d['rhatUUID'][0])
        user.is_employed = is_employed
        
        if 'rhatRnDComponent' in d and type(d['rhatRnDComponent']) is list:
            user.is_openshift = 'OpenShift' in d['rhatRnDComponent']

        if 'rhatSocialURL' in d and type(d['rhatSocialURL']) is list:
            for s in d['rhatSocialURL']:
                matches = re.search(r'^github->https?://github\.com/(.*)', str(s), re.IGNORECASE)
                if matches:
                    user.github = matches.group(1).strip().lower()
                    break

        def add_mail(key):
            if key in d and type(d[key]) is list and len(d[key]):
                mail = str(d[key][0]).lower()
                if mail not in user.emails:
                    user.emails.append(mail)

        add_mail('rhatPreferredAlias')
        add_mail('rhatPrimaryMail')
        add_mail('mail')
        if len(user.emails):
            user.primary_email = user.emails[0]
        
        return user

    @staticmethod
    def desired_attributes():
        """
        List of all LDAP attributes used to create the UserRecord object. This is passed into a search query
        to avoid returning all attributes, which is expensive.
        """
        return [
            'cn',
            'displayName',
            'sn',
            'uuid',
            'rhatUUID',
            'rhatRnDComponent',
            'rhatSocialURL',
            'rhatPreferredAlias',
            'rhatPrimaryMail',
            'mail',
        ]


    def __str__(self):
        return "{uid}:{full_name}:{primary_email}:{github}".format(
            uid=self.uid,
            full_name=self.full_name,
            primary_email=self.primary_email,
            github=self.github,
        )
