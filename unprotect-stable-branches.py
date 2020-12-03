#!/usr/bin/env python3

import datetime
import os
import sys

from github import Github, GithubException

GITHUB_ACCESS_TOKEN = os.environ.get('GITHUB_ACCESS_TOKEN')
if not GITHUB_ACCESS_TOKEN:
    print("You need a GITHUB_ACCESS_TOKEN environment variable defined.\n"
          "You can create a Github access token at https://github.com/settings/tokens.")
    sys.exit(1)

g = Github(GITHUB_ACCESS_TOKEN)
org = g.get_organization("charmed-kubernetes")
for repo in org.get_repos(type='all'):  # type: ‘all’, ‘public’, ‘private’, ‘forks’, ‘sources’, ‘member’
    try:
        branch = repo.get_branch(branch="stable")
    except GithubException as e:
        if e.status == 404:
            print('{} has no stable branch'.format(repo.name))
            continue
        else:
            raise
    branch.edit_protection(allow_force_pushes=True)
    print('Enabled force pushes for {}/stable'.format(repo.name))
