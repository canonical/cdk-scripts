#!/bin/env python3

from utils import CDKUtils


def main():
    utils = CDKUtils()
    teams = [
        "CDK",
    ]
    for team in teams:
        sizing_board = utils.get_sizing_board(team)
        sized_features = sizing_board.sized_features
        # Update team board
        team_board = utils.get_team_board(team)
        team_board.update_sizes(sized_features)
        # Update scrum board
        scrum_board = utils.get_scrum_board(team)
        scrum_board.update_sizes(sized_features)
        # Update product feedback
        feedback = utils.get_product_feedback(team)
        feedback.update_sizes(sized_features)


if __name__ == "__main__":
    main()
