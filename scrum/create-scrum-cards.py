#!/bin/env python3

import argparse

from utils import CDKUtils


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "release",
        help="Name of the release to create cards for",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    utils = CDKUtils()
    roadmap = utils.get_product_roadmap(args.release)
    roadmap_features = roadmap.get_features()
    teams = [
        "CDK",
        "MicroK8s",
    ]
    for team in teams:
        board = utils.get_scrum_board(team)
        board.create_release(args.release)
        board.create_cards(roadmap_features)
        board.tag_release(roadmap_features)

    team = "Kubeflow"
    roadmap = utils.get_product_roadmap(args.release, team=team)
    roadmap_features = roadmap.get_features()
    board = utils.get_scrum_board(team)
    board.create_release(args.release)
    board.create_cards(roadmap_features)
    board.tag_release(roadmap_features)


if __name__ == "__main__":
    main()
