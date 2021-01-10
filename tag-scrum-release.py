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
    scrum_boards = utils.get_scrum_boards()
    roadmap = utils.get_product_roadmap(args.release)
    roadmap_features = roadmap.get_features()
    for board in scrum_boards:
        board.create_release(args.release)
        board.tag_release(roadmap_features)


if __name__ == "__main__":
    main()
