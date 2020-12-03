#!/usr/bin/env python3

import datetime
import os
import sys

from github import Github

GITHUB_ACCESS_TOKEN = os.environ.get('GITHUB_ACCESS_TOKEN')
if not GITHUB_ACCESS_TOKEN:
    print("You need a GITHUB_ACCESS_TOKEN environment variable defined.\n"
          "You can create a Github access token at https://github.com/settings/tokens.")
    sys.exit(1)

g = Github(GITHUB_ACCESS_TOKEN)
org = g.get_organization("charmed-kubernetes")
for repo in org.get_repos(type='all'):  # type: ‘all’, ‘public’, ‘private’, ‘forks’, ‘sources’, ‘member’
    repo.edit(allow_squash_merge=True, allow_merge_commit=False, allow_rebase_merge=False)
