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
    parser.add_argument(
        "--clean",
        dest="clean",
        action="store_true",
    )
    return parser.parse_args()


def main():
    utils = CDKUtils()
    args = parse_args()
    # Product Teams
    if args.teams:
        teams = args.teams
    else:
        teams = ["CDK", "Kubeflow", "MicroK8s"]
    if args.skip:
        skip = args.skip
    else:
        skip = ["Reference Materials", "Misc", "Icebox", "In Review"]
    if args.board:
        boards = args.board
    else:
        boards = ["Backlog", "Scrum"]
    for team in teams:
        sizing_board = utils.get_sizing_board(team)
        if args.clean:
            print(f"Clearing Sizing board for {team}")
            sizing_board.clear_board()
        if "Scrum" in boards:
            print(f"Gathering from Scrum board for {team}")
            scrum_board = utils.get_scrum_board(team)
            features = scrum_board.get_features(attachments=True, skip=skip)
            filtered = filter(lambda x: not x.name.startswith("PR Review"), features)
            sizing_board.add_feature_cards(filtered)
        if "Backlog" in boards:
            print(f"Gathring from Backlog board for {team}")
            backlog_board = utils.get_backlog_board(team)
            backlog_board.logger.set_level("debug")
            sizing_board.add_feature_cards(
                backlog_board.get_features(attachments=True, skip=skip)
            )
        # sizing_board.truncate_lists()


if __name__ == "__main__":
    main()
