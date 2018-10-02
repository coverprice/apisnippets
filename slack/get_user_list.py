#!/bin/env python3

import os
from pprint import pprint
import sys
from slackclient import SlackClient
import pickle

def get_email_map():
    with open('email_map.txt', 'r') as fh:
        lines = fh.read().strip().split("\n")
    ret = {}
    for line in lines:
        l, r = line.split(" ")
        ret[r] = l
    return ret


def get_slack_client():
    with open(os.path.join(os.environ['HOME'], '.secrets/slack_token'), 'r') as fh:
        token = fh.read().strip()
    return SlackClient(token)


def get_all_users(slackclient):
    PICKLE_FILE = 'userlist.pickle'
    if os.path.isfile(PICKLE_FILE):
        with open(PICKLE_FILE, 'rb') as fh:
            return pickle.load(fh)
    
    user_list = sc.api_call("users.list")
    with open(PICKLE_FILE, 'wb') as fh:
        pickle.dump(user_list, fh)
    return user_list


def get_user_name(u):
    p = u['profile']
    if 'real_name_normalized' in p and len(p['real_name_normalized']) > 0:
        return p['real_name_normalized']
    if 'display_name_normalized' in p and len(p['display_name_normalized']) > 0:
        return p['display_name_normalized']
    return "{0} {1}".format(p['first_name'], p['last_name']).strip()


sc = get_slack_client()
users = get_all_users(sc)
users = sorted(users['members'], key=lambda rec:str.lower(get_user_name(rec)))
active_users = [
    user
    for user in users
    if user['deleted'] is False and
        user['is_bot'] is False and
        'email' in user['profile'] and
        user['profile']['email'].lower().endswith('@coreos.com')
]

def update_user(slackclient, user_id, email):
    print("Updating {} to {}".format(user_id, email))
    response = slackclient.api_call(
        'users.profile.set',
        user=user_id,
        profile={ 'email': email },
    )

email_map = get_email_map()
for user in active_users:
    p = user['profile']
    new_email = email_map[p['email']]
    print('{0:13} {1:30} {2:30} {3:30} {4:30}'.format(user['id'], p['real_name_normalized'], p['display_name_normalized'], p['email'], new_email))
    # update_user(sc, user['id'], new_email)
