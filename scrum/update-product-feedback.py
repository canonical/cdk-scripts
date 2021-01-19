#!/bin/env python3

from utils import CDKUtils


def main():
    utils = CDKUtils()
    teams = [
        "CDK",
    ]
    for team in teams:
        # Get boards
        team_board = utils.get_team_board(team)
        scrum_board = utils.get_scrum_board(team)
        # Update product feedback
        print(f"Updating Product Feedback: {team}")
        feedback = utils.get_product_feedback(team)
        features = team_board.get_features(attachments=False)
        features.extend(scrum_board.get_features(attachments=False))
        feedback.update_features(features)


if __name__ == "__main__":
    main()
