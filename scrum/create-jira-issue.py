#!/bin/env python3

import argparse

from utils import CDKUtils


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--teams",
        nargs="*",
        help="Team names to process",
    )
    parser.add_argument(
        "--skip",
        nargs="*",
        help="Columns to skip during gathering from boards",
    )
    parser.add_argument(
        "--board",
        choices=["Backlog", "Scrum"],
        help="Board to gather from",
    )
    return parser.parse_args()


def main():
    utils = CDKUtils()
    args = parse_args()
    # Product Teams
    if args.teams:
        teams = args.teams
    else:
        teams = ["CDK"]
        # teams = ["CDK", "Kubeflow", "MicroK8s"]
    if args.skip:
        skip = args.skip
    else:
        skip = [
            "Reference Materials",
            "Misc",
            "Icebox",
            "In Review",
            "Product Feedback",
            "In progress",
            "Blocked",
        ]
    if args.board:
        boards = args.board
    else:
        boards = ["Scrum"]
        # boards = ["Backlog", "Scrum"]
    for team in teams:
        project = utils.get_jira_project(team)
        project.logger.set_level("debug")
        # print(jira_board.jira.search_issues('project=CK'))
        print(f"Team: {team}" f"Issues: {project.all_issues}")
        if "Scrum" in boards:
            print(f"Gathering from Scrum board for {team}")
            scrum_board = utils.get_scrum_board(team)
            features = scrum_board.get_features(attachments=True, skip=skip)
            filtered = filter(lambda x: not x.name.startswith("PR Review"), features)
            project.import_trello_issues(filtered)
        # if "Backlog" in boards:
        #     print(f"Gathring from Backlog board for {team}")
        #     backlog_board = utils.get_backlog_board(team)
        #     backlog_board.logger.set_level("debug")


if __name__ == "__main__":
    main()
