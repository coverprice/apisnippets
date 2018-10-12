#!/bin/env python3

import functools
import requests
from pprint import pprint
import os


@functools.lru_cache()
def get_api_key():
    if 'GITHUB_API_KEY' in os.environ:
        return os.environ['GITHUB_API_KEY']
    if 'HOME' in os.environ:
        path = os.path.join(os.environ['HOME'], '.secrets', 'github_api_key')
        if os.path.exists(path):
            with open(path, 'rb') as fh:
                return fh.read().decode('utf-8').strip()

    raise Exception('Could not find Github API key in envvar GITHUB_API_KEY or file ~/.secrets/github_api_key')


def run_query(query, variables):
    request = requests.post(
        'https://api.github.com/graphql',
        json={'query': query, 'variables': variables},
        headers={"Authorization": "bearer {0}".format(get_api_key())},
    )
    if request.status_code != 200:
        pprint(vars(request))
        raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))

    ret = request.json()
    if 'errors' in ret and len(ret['errors']):
        pprint(ret)
        raise Exception("Query had errors: {}".format(
            "\n".join(
                [error['message'] for error in ret['errors']]
            )
        ))

    return ret['data']
