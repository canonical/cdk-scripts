#!/usr/bin/env python3

import argparse

from utils import CDKUtils
from roadmap.logging import Logger


TEAMS = ["CDK", "MicroK8s", "Kubeflow"]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry-run, and only report changes that would be made",
    )
    parser.add_argument(
        "--teams", "-t",
        choices=TEAMS, default=TEAMS, nargs="*",
        help="Team names to process",
    )
    return parser.parse_args()


def main():
    logger = Logger()
    logger.set_level("debug")
    args = parse_args()
    utils = CDKUtils(dry_run=args.dry_run)
    for team in args.teams:
        logger.info(f"Processing team {team}")
        repo_group = utils.get_repo_group(team)
        prs = repo_group.get_external_prs()
        if not prs:
            continue
        jira_project = utils.get_jira_project(team)
        jira_project.import_external_prs(prs)


if __name__ == "__main__":
    main()
