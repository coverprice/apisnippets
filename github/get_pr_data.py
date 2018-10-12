#!/bin/env python3
# Pulls down metadata about Pull Requests from the given set of repos, and writes it to a CSV-format file.
# This is useful in determining how often tests may need to be run.

import csv
import sys

REPOS = """
https://github.com/coreos/awscli
https://github.com/kubernetes-incubator/bootkube
https://github.com/coreos-inc/tectonic-operators/tree/master/operator/node-controller
https://github.com/coreos/kubecsr/
https://github.com/coreos/etcd
https://github.com/coreos/kubernetes
https://github.com/coreos-inc/tectonic-operators/tree/master/operator/kube-core
https://github.com/coreos-inc/tectonic-operators/tree/master/operator/kube-core
https://github.com/coreos-inc/tectonic-operators/tree/master/operator/channel
https://github.com/coreos-inc/tectonic-prometheus-operator
https://github.com/coreos-inc/tectonic-cluo-operator
https://github.com/coreos/tectonic-torcx
https://github.com/coreos-inc/tectonic-operators/tree/master/operator/kube-addon
https://github.com/operator-framework/operator-lifecycle-manager
https://github.com/coreos-inc/tectonic-operators/tree/master/operator/ingress
https://github.com/coreos-inc/tectonic-operators/tree/master/operator/utility
https://github.com/coreos-inc/tectonic-operators/tree/master/operator/network
https://github.com/coreos/kubecsr/
"""

def get_repo_names():
    return [
        repo_url[len('https://github.com/'):].split('/')[:2]
        for repo_url in REPOS.strip().split("\n")
    ]

def main():
    repos = get_repo_names()
    csvout = csv.writer(
        sys.stdout,
        delimiter=',',
        quotechar='|',
        quoting=csv.QUOTE_MINIMAL,
    )
    csvout.writerow([
        'Repo',
        'PR number',
        'Title',
        'Merge status',
        'Created datetime',
        'Closed datetime',
    ])
    for (orgname, reponame) in repos:
        for pr in githubapi.api.get_prs(orgname=orgname, reponame=reponame):
            csvout.writerow([
                '{orgname}/{reponame}'.format(orgname=orgname, reponame=reponame),
                pr['number'],
                pr['title'],
                'Merged' if pr['merged'] else 'Not Merged',
                pr['createdAt'],
                pr['closedAt'],
            ])


if __name__ == '__main__':
    main()
