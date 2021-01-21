#!/bin/env python3

import argparse

from utils import CDKUtils


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--teams",
        nargs='*',
        help="Team names to process",
    )
    return parser.parse_args()


def main():
    utils = CDKUtils()
    args = parse_args()
    # Product Teams
    if args.teams:
        teams = args.teams
    else:
        teams = ["CDK", "Kubeflow", "Test", "MicroK8s"]
    for team in teams:
        scrum_board = utils.get_scrum_board(team)
        backlog_board = utils.get_backlog_board(team)
        sizing_board = utils.get_sizing_board(team)
        sizing_board.add_feature_cards(backlog_board.get_features(attachments=True))
        sizing_board.add_feature_cards(scrum_board.get_features(attachments=True))
        # sizing_board.truncate_lists()


if __name__ == "__main__":
    main()
