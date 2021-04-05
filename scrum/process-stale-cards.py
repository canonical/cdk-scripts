#!/bin/env python3
import datetime

from utils import CDKUtils


def main():
    utils = CDKUtils()
    teams = [
        "CDK",
        "MicroK8s",
        "Kubeflow",
    ]
    for team in teams:
        # Scrum board: label stale cards and move inactive+stale cards to backlog
        scrum_board = utils.get_scrum_board(team)
        scrum_board.logger.set_level("info")
        scrum_board.label_stale_cards()
        scrum_board.logger.set_level("warning")
        move_delta = datetime.timedelta(days=10)
        inactive_cards = scrum_board.get_stale_cards(
            lists=scrum_board.IN_PROGRESS_LISTS, delta=move_delta
        )
        backlog_board = utils.get_backlog_board(team)
        for list in backlog_board.lists:
            if list.name == "Backlog":
                inactive_list = list
        for card in inactive_cards:
            try:
                next(
                    filter(
                        lambda x: x.name == scrum_board.STALE_LABEL_NAME
                        and x.color == scrum_board.STALE_LABEL_COLOR,
                        card.labels,
                    )
                )
                # Card has the stale label
                print(f"Found inactive and stale card moving: {team}:{card.name}")
                card.change_board(backlog_board.id, inactive_list.id)
            except (StopIteration, TypeError):
                # No lables, or no stale label
                pass


if __name__ == "__main__":
    main()
