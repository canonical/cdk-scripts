#!/bin/env python3

from utils import CDKUtils


def main():
    utils = CDKUtils()
    teams = [
        "CDK",
    ]
    for team in teams:
        print(f"Updating Sizes for {team}")
        print("Getting sizes from Sizing Board")
        sizing_board = utils.get_sizing_board(team)
        sized_features = sizing_board.sized_features
        # Update team board
        print("Updating Backlog")
        team_board = utils.get_team_board(team)
        team_board.update_sizes(sized_features)
        # Update scrum board
        print("Updating Scrum Board")
        scrum_board = utils.get_scrum_board(team)
        scrum_board.update_sizes(sized_features)
        # Update product feedback
        print("Updating Product Feedback")
        feedback = utils.get_product_feedback(team)
        feature_sizes = team_board.get_features(attachments=False)
        feature_sizes.extend(scrum_board.get_features(attachments=False))
        feedback.update_features(feature_sizes)


if __name__ == "__main__":
    main()
