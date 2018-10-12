#!/usr/bin/env python3

import ldap3
import re
from pprint import pprint
import argparse
import sys
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'libs', 'python'))
import dpp.ldap

def parse_args():
    parser = argparse.ArgumentParser(description='Searches for an LDAP user by uid or email')
    parser.add_argument('criteria', action="store")
    return parser.parse_args()

args = parse_args()

criteria = args.criteria.lower().strip()

user_searcher = dpp.ldap.UserSearcher()
if criteria.endswith('@redhat.com'):
    user = user_searcher.find_by_email(criteria)
else:
    user = user_searcher.find_by_uid(criteria)
if user is None:
    print("'{}' not found.".format(criteria))
    sys.exit(1)

print(user)
