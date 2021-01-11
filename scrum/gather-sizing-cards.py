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
        sizing_board = utils.get_sizing_board(team)
        sizing_board.setup_lists()
        sizing_board.add_team_cards(team_board.get_features())
        sizing_board.add_feedback_cards(feedback.get_features())

    # Non-product teams
    for team in [
        "Test",
    ]:
        team_board = utils.get_team_board(team)
        sizing_board = utils.get_sizing_board(team)
        sizing_board.setup_lists()
        sizing_board.add_team_cards(team_board.get_features())


if __name__ == "__main__":
    main()
