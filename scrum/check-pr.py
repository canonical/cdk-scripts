#!/bin/env python3

from utils import CDKUtils


def main():
    utils = CDKUtils()
    teams = ["CDK", "MicroK8s", "Kubeflow"]
    for team in teams:
        repo_group = utils.get_repo_group(team)
        # repo_group.logger.set_level("debug")
        reviews = repo_group.get_unreviewed_pulls()
        scrum_board = utils.get_scrum_board(team)
        scrum_board.add_pull(reviews)


if __name__ == "__main__":
    main()
