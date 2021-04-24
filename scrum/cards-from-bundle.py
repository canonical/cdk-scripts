#!/bin/env python3

import argparse
from pathlib import Path

import yaml

from utils import CDKUtils


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--team",
        choices=["CDK", "Kubeflow", "MicroK8s"],
        required=True,
        help="Team names to process",
    )
    parser.add_argument(
        "--board",
        choices=["Backlog", "Scrum", "Sizing"],
        required=True,
        help="Board add to",
    )
    parser.add_argument(
        "--list",
        required=True,
        help="Create cards in given list",
    )
    parser.add_argument(
        "--bundle",
        required=True,
        help="Path to the bundle",
    )
    return parser.parse_args()


def main():
    utils = CDKUtils()
    args = parse_args()
    # Product Teams
    team = args.team
    board = args.board
    list = args.list

    if args.board == "Sizing":
        board = utils.get_sizing_board(team)
    elif args.board == "Backlog":
        board = utils.get_backlog_board(team)
    elif args.board == "Scrum":
        board = utils.get_scrum_board(team)

    for info in card_generator(args.bundle):
        print(f"Adding card: {info['title']}")
        board.add_card(name=info["title"], description=info["body"],
                       list=args.list)


def card_generator(bundle):
    bundle_path = Path(bundle)
    contents = yaml.safe_load(bundle_path.read_text())
    for name in contents["applications"]:
        title = f"Convert {name} to sidecar"
        body = """We need to convert to sidecar charms.

Some charms may have issues in the coverstion. If a Juju issue is encounterd a bug should be opened, attached to this card and add to the Juju K8s sync for review. This
card can be moved to blocked if it can not proceed.

Definition of done:

* charm is merged with sidecar pattern
* unit tests run on PR
* integration tests run on PR
* testing via pytest-operator
        """
        yield {"title": title, "body": body}


if __name__ == "__main__":
    main()
