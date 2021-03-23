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
        teams = ["CDK", "Kubeflow", "Test", "MicroK8s"]
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
            features = scrum_board.get_features(attachments=True)
            filtered = filter(lambda x: not x.name.startswith("PR Review"), features)
            sizing_board.add_feature_cards(filtered)
        if "Backlog" in boards:
            print(f"Gathring from Backlog board for {team}")
            backlog_board = utils.get_backlog_board(team)
            sizing_board.add_feature_cards(backlog_board.get_features(attachments=True))
        sizing_board.truncate_lists()


if __name__ == "__main__":
    main()
