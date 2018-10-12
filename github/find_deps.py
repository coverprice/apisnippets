#!/bin/env python3

class DiscRepo(object):
    def __init__(self, url, name, path):
        self.url = url
        self.name = name
        self.path = path

    @classmethod
    def find(name) -> DiscRepo:
        """
        TODO
        """
        raise NotImplemented()
        return DiscRepo or error


class Dependency(object):
    def __init__(self, dep_type: str, target_repo_id: str):
        assert(dep_type in ["vendor", "godep", "glide"])
        self.dep_type = dep_type
        self.target_repo_id = target_repo_id


class Repository(object):
    def __init__(self, repo_id: str, name: str, disc_repo: DiscRepo):
        self.repo_id = repo_id   # unique identifier (github URL)
        self.name = name        # Short name of this repo (i.e. last part of the URL)
        self.disc_repo = disc_repo        # Short name of this repo (i.e. last part of the URL)
        self.depends_on = []     # List of Dependency objects
        self.used_by = []       # List of repository names

    def add_dependency(dep: Dependency) -> None:
        """
        TODO
        """
        if dependency already exists, return
        raise NotImplemented()


class RepoGraph(object):
    def __init__(self):
        self.graph = {}     # Repository

    def add_repo(disc_repo: DiscRepo) -> Repository:
        repo_id = disc_repo.url
        if repo_id in self.graph:
            return self.graph[repo_id]
        repo = Repository(
            repo_id=disc_repo.url,
            name=disc_repo.name,
            disc_repo=disc_repo,
        )
        self.graph[repo.repo_id] = repo
        return repo

    def find_deps(repo: Repository):
        for each vendor/github.com/[coreos|coreos-inc|operator-framework]/*
            disc_repo = DiscRepo.find(name)
            dep_repo = self.add_repo(disc_repo)
            repo.add_dependency(dep_type="vendored", dep_repo)
        if glide.lock exists:
            parse
            for each dep that matches coreos/coreos-inc/operator-framework:
                disc_repo = DiscRepo.find(name)
                repo.add_dependency(dep_type="glide", dep_repo=disc_repo)
                add
#   look for glide.lock
#   if found, extract

def add_repo(repos, repo_name):
  find_repo
  make empty Repo
  find_dependencies(repos, repo_id)
  

def make_graph(repo_names):
    repos = {}
    for repo_name in repo_names:
        name, url = find_repo
        add_repo(repos, repo_name)

# for each repo
#   find the repo
#     if not found, error
# 
#   look for vendor/github.com/[coreos|coreos-inc]/*
#   look for glide.lock
#   if found, extract
# look for Godep.lock

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
