#!/bin/env python3

from utils import CDKUtils


def main():
    utils = CDKUtils()
    # Product Teams
    for team in [
        "CDK",
    ]:
        team_board = utils.get_team_board(team)
        feedback = utils.get_product_feedback(team)
        feedback.add_titles()
        team_board.setup_board()
        team_board.add_feedback_cards(feedback.get_features())


if __name__ == "__main__":
    main()
