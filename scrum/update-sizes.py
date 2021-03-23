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
        "--board",
        choices=["Backlog", "Scrum", "Product"],
        help="Board to update",
    )
    parser.add_argument(
        "--list",
        help="Create missing cards in given list",
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
    if args.board:
        boards = args.board
    else:
        boards = ["Backlog", "Scrum", "Product"]
    if args.list:
        new_list = args.list
    else:
        new_list = None
    for team in teams:
        print(f"Updating Sizes for {team}")
        print("Getting sizes from Sizing Board")
        sizing_board = utils.get_sizing_board(team)
        sizing_board.logger.set_level("debug")
        sized_features = sizing_board.get_features(attachments=True)
        if "Backlog" in boards:
            # Update backlog board
            print("Updating Backlog")
            backlog_board = utils.get_backlog_board(team)
            backlog_board.update_features(sized_features, new_list=new_list)
            backlog_board.update_sizes(sized_features)
        if "Scrum" in boards:
            # Update scrum board
            print("Updating Scrum Board")
            scrum_board = utils.get_scrum_board(team)
            scrum_board.logger.set_level("debug")
            scrum_board.update_features(sized_features, new_list=new_list)
            scrum_board.update_sizes(sized_features)
        if "Product" in boards:
            # Update product feedback
            print("Updating Product Feedback")
            feedback = utils.get_product_feedback(team)
            feature_sizes = backlog_board.get_features()
            feature_sizes.extend(scrum_board.get_features())
            feedback.update_features(feature_sizes)


if __name__ == "__main__":
    main()
