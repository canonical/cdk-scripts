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
    return parser.parse_args()


def main():
    utils = CDKUtils()
    args = parse_args()
    # Product Teams
    if args.teams:
        teams = args.teams
    else:
        teams = ["CDK", "Kubeflow", "MicroK8s"]
    for team in teams:
        backlog_board = utils.get_backlog_board(team)
        feedback = utils.get_product_feedback(team)
        feedback.add_titles()
        backlog_board.logger.set_level("debug")
        backlog_board.add_feedback_cards(feedback.get_features())


if __name__ == "__main__":
    main()
