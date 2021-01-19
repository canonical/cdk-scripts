#!/bin/env python3

from utils import CDKUtils


def main():
    utils = CDKUtils()
    # Product Teams
    for team in [
        # "CDK",
        "Kubeflow",
    ]:
        scrum_board = utils.get_scrum_board(team)
        backlog_board = utils.get_backlog_board(team)
        feedback = utils.get_product_feedback(team)
        feedback.add_titles()
        sizing_board = utils.get_sizing_board(team)
        sizing_board.add_feature_cards(backlog_board.get_features(attachments=True))
        sizing_board.add_feature_cards(scrum_board.get_features(attachments=True))
        # sizing_board.truncate_lists()

    # Non-product teams
    # for team in [
    #     "Test",
    # ]:
    #     team_board = utils.get_team_board(team)
    #     sizing_board = utils.get_sizing_board(team)
    #     sizing_board.add_team_cards(team_board.get_features())


if __name__ == "__main__":
    main()
