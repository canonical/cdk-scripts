#!/usr/bin/env python3

"""
Close a milestone and related bugs across all Charmed Kubernetes projects.

usage: ./close-milestone.py 1.15+ck1 --date 2019-08-15

This will find every project under the Charmed Kubernetes project group that
has an active '1.15+ck1' milestone, set all 'Fix Committed' bugs to
'Fix Released', and release/close/deactivate the milestone with the given
date (uses today's date if no date is provided).

"""

import argparse
import datetime

from launchpadlib import errors as lperrors
from launchpadlib import launchpad


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'milestone',
        help='Name of milestone to close'
        )
    parser.add_argument(
        '--date',
        help='Date milestone was closed (YYYY-mm-dd)',
        default=datetime.datetime.now().strftime('%Y-%m-%d')
        )
    return parser.parse_args()


def get_milestone(project_series, milestone_name):
    for milestone in project_series.active_milestones:
        if milestone.name == milestone_name:
            return milestone
    return None


def main():
    args = parse_args()

    app = 'Charmed Kubernetes Launchpad Bot'
    env = 'production'
    lp = launchpad.Launchpad.login_with(app, env)

    for project in lp.project_groups['charmed-kubernetes'].projects:
        print('%s: ' % project.name, end=''),
        trunk = project.getSeries(name='trunk')
        if not trunk:
            print('skipping, no trunk series')
            continue

        milestone = get_milestone(trunk, args.milestone)
        if not milestone:
            print('skipping, no active milestone named %s' % args.milestone)
            continue

        bugs = project.searchTasks(milestone=milestone, status='Fix Committed')
        if bugs:
            count = len(bugs)
            for bug in bugs:
                bug.status = 'Fix Released'
                bug.lp_save()
            print('closed %s bugs' % count)

        if not milestone.date_targeted:
            milestone.date_targeted = args.date
        if not milestone.release:
            milestone.createProductRelease(date_released=args.date)
        milestone.is_active = False
        milestone.lp_save()


if __name__ == '__main__':
    main()
