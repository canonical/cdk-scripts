#!/bin/env python3

import argparse

from utils import CDKUtils


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "release",
        help="Name of the release to update",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    utils = CDKUtils()
    roadmap = utils.get_product_roadmap(args.release)
    teams = [
        "CDK",
        "MicroK8s",
    ]
    scrum_features = []
    for team in teams:
        board = utils.get_scrum_board(team)
        scrum_features.extend(board.get_release_features(args.release))
        roadmap.update_features(scrum_features)

    team = "Kubeflow"
    roadmap = utils.get_product_roadmap(args.release, team=team)
    scrum_board = utils.get_scrum_board(team)
    roadmap.update_features(scrum_board.get_release_features(args.release))


if __name__ == "__main__":
    main()
