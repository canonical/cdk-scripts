#!/usr/bin/env python3

"""
Count Field SLA bugs in Charmed Kubernetes.

usage: ./field-sla.py

The output of this script is parsed by Telegraf and fed to InfluxDB,
to be displayed on the Kubernetes Grafana dashboard.

"""

import datetime

from launchpadlib import errors as lperrors
from launchpadlib import launchpad


def main():
    app = 'Charmed Kubernetes Launchpad Bot'
    env = 'production'
    lp = launchpad.Launchpad.login_anonymously(app, env)

    bug_subscribers = [
        'field-medium',
        'field-high',
        'field-critical',
    ]

    bug_statuses = [
        'New',
        'Confirmed',
        'Triaged',
        'In Progress'
    ]

    for name in bug_subscribers:
        person = lp.people[name]
        severity = name.split('-')[-1]
        count = 0

        project_group = lp.project_groups['charmed-kubernetes']
        bugs = project_group.searchTasks(status=bug_statuses, bug_subscriber=person)
        if bugs:
            count += len(bugs)

        print('field_sla_bugs,subscriber={},severity={} total_bugs={}i'.format(name, severity, count))


if __name__ == '__main__':
    main()
