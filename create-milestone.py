#!/usr/bin/env python3

"""
Create a milestone across all Charmed Kubernetes projects.

usage: ./create-milestone.py 1.16 --date 2019-09-23

"""

import argparse
import datetime

from launchpadlib import errors as lperrors
from launchpadlib import launchpad


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'milestone',
        help='Name of milestone to create'
        )
    parser.add_argument(
        '--date',
        help='Target release date for milestone (YYYY-MM-DD)',
        default=None
        )
    return parser.parse_args()


def get_milestone(project_series, milestone_name):
    for milestone in project_series.all_milestones:
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
        if milestone:
            print('skipping, milestone %s already exists' % args.milestone)
            continue

        trunk.newMilestone(name=args.milestone, date_targeted=args.date)
        print('milestone created')


if __name__ == '__main__':
    main()
