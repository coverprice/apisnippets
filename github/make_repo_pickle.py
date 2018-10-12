#!/bin/env python3

from pprint import pprint
import pickle
import sys
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'libs', 'python'))

import dpp.github

def main():
    repos = dpp.github.api.get_repos("coreos") + dpp.github.api.get_repos("coreos-inc")
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
