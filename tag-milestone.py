#!/usr/bin/env python3

"""
Apply a tag to all bugs in a milestone that match a given bug status.

Bugs that already have the tag will be skipped.

"""

import argparse
import datetime
import sys

from launchpadlib import errors as lperrors
from launchpadlib import launchpad


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        'milestone',
        help='Name of milestone',
        )
    parser.add_argument(
        '--tag',
        help='Name of tag to add (default: "backport-needed")',
        default='backport-needed',
        )
    parser.add_argument(
        '--status',
        help='Bug status filter. Only bugs with this status will be tagged. (default: "Fix Committed")',
        default='Fix Committed',
        )
    return parser.parse_args()


def main():
    args = parse_args()

    app = 'Charmed Kubernetes Launchpad Bot'
    env = 'production'
    lp = launchpad.Launchpad.login_with(app, env)

    project_group = lp.project_groups['charmed-kubernetes']
    milestone = project_group.getMilestone(name=args.milestone)
    if not milestone:
        sys.exit("Milestone doesn't exist")

    bug_tasks = project_group.searchTasks(milestone=milestone, status=args.status)

    for bug_task in bug_tasks:
        bug = bug_task.bug
        if args.tag in bug.tags:
            continue
        bug.tags += [args.tag]
        bug.lp_save()
        print('Tagged bug %s' % bug.id)


if __name__ == '__main__':
    main()
