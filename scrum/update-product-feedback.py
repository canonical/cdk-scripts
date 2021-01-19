#!/bin/env python3

from utils import CDKUtils


def main():
    utils = CDKUtils()
    teams = [
        # "CDK",
        "Kubeflow",
    ]
    for team in teams:
        # Get boards
        backlog_board = utils.get_backlog_board(team)
        scrum_board = utils.get_scrum_board(team)
        # Update product feedback
        print(f"Updating Product Feedback: {team}")
        feedback = utils.get_product_feedback(team)
        features = backlog_board.get_features()
        features.extend(scrum_board.get_features())
        feedback.update_features(features)


if __name__ == "__main__":
    main()
