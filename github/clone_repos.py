#!/bin/env python3
"""
Clones all the repos from various (hard-coded) orgs into a sub-directory
"""

import functools
import json
import git
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'libs', 'python'))
import dpp.github

def clone_repo(repo_dir, repo_url):
    if os.path.exists(repo_dir):
        if os.path.exists(os.path.join(repo_dir, '.git')):
            print("Skipping, already cloned")
            return
    else:
        os.makedirs(repo_dir)

    progress = git.remote.RemoteProgress()
    repo = git.Repo.clone_from(
        url=repo_url + '.git',
        to_path=repo_dir,
    )


def main():
    orgs = [
        "coreos",
        "coreos-inc",
        "operator-framework",
    ]
    repos = functools.reduce(lambda x,y: x+y, [dpp.github.api.get_repos(org) for org in orgs])
    repos = sorted(repos, key=lambda x: x['name'])

    cwd = os.path.dirname(os.path.abspath(__file__))
    num_repos = len(repos)
    for idx, repo in enumerate(repos):
        repo_dir = os.path.join(cwd, 'repos', repo['name'])
        repo_url = repo['url']
        print("{idx:>{width}}/{num_repos}: Cloning {repo_url} into {repo_dir}".format(
            idx=idx + 1,
            num_repos=len(repos),
            width=len(str(len(repos))),
            repo_url=repo_url,
            repo_dir=repo_dir,
        ))
        clone_repo(repo_dir, repo_url)


if __name__ == '__main__':
    main()
