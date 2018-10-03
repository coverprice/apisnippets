#!/bin/env python3

from pprint import pprint
import sys
import os

from .graphql import run_query


def get_prs(orgname, reponame):
    query = """
    query GetPRs ($orgname: String!, $reponame: String!, $first: Int, $after: String) {
      repository(name: $reponame, owner: $orgname) {
        pullRequests(
            first: $first,
            after: $after,
            states: [CLOSED, MERGED],
            orderBy: {field: UPDATED_AT, direction: DESC}
        ) {
          pageInfo {
            endCursor
            hasNextPage
            hasPreviousPage
            startCursor
          }
          nodes {
            number
            createdAt
            merged
            closed
            closedAt
            title
          }
        }
      }
    }
    """
    query_vars = """
    {
      "orgname": "%s",
      "reponame": "%s",
      "first": %s,
      "after": %s
    }
    """
    results = []
    first = 100
    after = "null"

    while True:
        result = run_query(query, query_vars % (orgname, reponame, first, after))
        data = result['repository']['pullRequests']
        results += [
            repo
            for repo in data['nodes']
        ]
        if not data['pageInfo']['hasNextPage']:
            break
        first = "null"
        after = '"{cursor}"'.format(cursor=data['pageInfo']['endCursor'])

    return results


def get_repos(orgname):
    query = """
    query GetRepos ($orgname: String!, $first: Int, $after: String) {
      organization(login: $orgname) {
        repositories(first: $first, after: $after, orderBy: {field: NAME, direction: ASC}) {
          pageInfo {
            endCursor
            hasNextPage
            hasPreviousPage
            startCursor
          }
          nodes {
            name
            description
            owner {
              login
            }
            isFork
            isPrivate
            url
          }
        }
      }
    }
    """
    query_vars = """
    {
      "orgname": "%s",
      "first": %s,
      "after": %s
    }
    """
    results = []
    first = 100
    after = "null"

    while True:
        result = run_query(query, query_vars % (orgname, first, after))
        data = result['organization']['repositories']
        results += [
            repo
            for repo in data['nodes']
        ]
        if not data['pageInfo']['hasNextPage']:
            break
        first = "null"
        after = '"{cursor}"'.format(cursor=data['pageInfo']['endCursor'])

    for i in range(0, len(results)):
        results[i]['organization'] = results[i]['owner']['login']
        del results[i]['owner']

    return results
