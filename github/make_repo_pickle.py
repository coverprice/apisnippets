#!/bin/env python3

from pprint import pprint
import sys
import pickle
import os

import githubapi.api

def main():
    repos = githubapi.api.get_repos("coreos") + githubapi.api.get_repos("coreos-inc")
    repos = sorted(repos, key=lambda x: x['name'])
    print(len(repos))
    pprint(repos)
    save(repos)


def _get_pickle_file():
    cwd = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(cwd, 'repos.pickle')

def save(repos):
    pickle.dump(repos, open(_get_pickle_file(), 'wb'))

def load():
    return pickle.load(open(_get_pickle_file(), 'rb'))


if __name__ == '__main__':
    main()
