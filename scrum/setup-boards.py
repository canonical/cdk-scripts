#!/bin/env python3

from utils import CDKUtils


def main():
    utils = CDKUtils()
    teams = [
        "CDK",
        # "Test",
        # "Kubeflow",
        # "MicroK8s",
    ]
    for team in teams:
        board = utils.get_scrum_board(team)
        board.setup_board()
        board = utils.get_team_board(team)
        board.setup_board()
        board = utils.get_sizing_board(team)
        board.setup_board()
        board.clear_board()


if __name__ == "__main__":
    main()
