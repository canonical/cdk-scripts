from functools import lru_cache

from roadmap.feature import TrelloFeature, FeatureStatus
from roadmap.logging import Logger
from trello import TrelloClient

cache = lru_cache(maxsize=None)


class TeamBoard:
    def __init__(self, client, name=None, id=None):
        if not name and not id:
            raise ValueError("Either a board name or id must be provided")
        self.id = id
        self.name = name
        self.client = client
        self.logger = Logger()
        self.board = self._get_board()

    def _get_board(self):
        if self.id:
            return self.client.get_board(self.id)

        all_boards = self.client.list_boards()
        for board in all_boards:
            if board.name.lower() == self.name.lower():
                self.id = board.id
                return board
        raise ValueError(f"Board {self.name} not in {all_boards}")


class Utils:
    def __init__(self, api_key, api_secret, boards):
        self.client = TrelloClient(api_key, api_secret)
        self.board_names = boards
        self.logger = Logger()

    @property
    def boards(self):
        all_boards = self.client.list_boards()
        return filter(lambda x: x.name in self.board_names, all_boards)

    def create_release(self, release):
        """Create A new release list on all boards"""
        for board in self.boards:
            pos = None
            all_lists = board.all_lists()
            for card_list in all_lists:
                if release == card_list.name:
                    return
            for card_list in all_lists:
                if "In progress".lower() == card_list.name.lower():
                    pos = card_list.pos - 1
                    break
            board.add_list(release, pos)
            board.add_label(release, "green")
            board.add_label(release, "blue")
            board.add_label(release, "red")
            board.add_label(release, "black")
            board.add_label(release, "orange")

    def create_feature_cards(self, roadmap_features, category_mapping):
        """Create cards for a list of roadmap features"""
        boards = list(self.boards)
        for feature in roadmap_features:
            board = next(
                filter(lambda x: x.name == category_mapping[feature.category], boards)
            )
            # label = self.get_label(board, name=feature.release, color="green")
            if self.get_card(board=board, name=feature.name, label_txt=feature.release):
                # Card already exists
                continue
            card_list = self.get_list_by_name(board, feature.release)
            label = self.get_label(board, name=feature.release, color="green")
            card_list.add_card(name=feature.name, labels=[label], position="bottom")

    def get_card(self, board, name, label=None, label_txt=None):
        cards = board.get_cards()
        for card in cards:
            if card.name == name:
                if label or label_txt:
                    label_found = False
                    for clabel in card.labels:
                        if label and clabel.id == label.id:
                            label_found = True
                        if label_txt and clabel.name == label_txt:
                            label_found = True
                    if not label_found:
                        continue
                return card
        return None

    def get_label(self, board, name, color):
        """Return a label by name"""
        for label in board.get_labels():
            if label.name == name and label.color == color:
                return label
        return None

    def get_list_by_name(self, board, name):
        """Return a list from a board by name"""
        for list in board.all_lists():
            if list.name.lower() == name.lower():
                return list
        return None

    def get_blackhole(self):
        all_boards = self.client.list_boards()
        for board in all_boards:
            if board.name == "Blackhole":
                return board

    def blackhole_lists(self, list_name):
        boards = list(self.boards)
        blackhole = self.get_blackhole()
        for board in boards:
            while True:
                victom = self.get_list_by_name(board, list_name)
                if victom:
                    victom.move_to_board(blackhole)
                else:
                    break

    def delete_all_cards(self, list_name):
        boards = list(self.boards)
        for board in boards:
            target_list = self.get_list_by_name(board, list_name)
            if target_list:
                cards = target_list.list_cards()
                for card in cards:
                    card.delete()

    def get_card_status(self, board, release, card):
        card_list = board.get_list(card.list_id)
        if card_list.name.lower() == "done":
            done = True
        else:
            done = False
        if card_list.name.lower() == release:
            started = False
        else:
            started = True
        for label in card.labels:
            if label.name == release:
                planned = True
                at_risk = False
                miss = False
                dropped = False
                if label.color == "blue":
                    planned = False
                elif label.color == "orange":
                    at_risk = True
                elif label.color == "red":
                    miss = True
                elif label.color == "black":
                    dropped = True
        return FeatureStatus(started, done, planned, at_risk, miss, dropped)

    def get_feature_cards(self, release):
        boards = list(self.boards)
        features = []
        for board in boards:
            release_labels = []
            for color in ["green", "blue", "orange", "red", "black"]:
                label = self.get_label(board, release, color)
                if label:
                    release_labels.append(label)
            for card in board.visible_cards():
                label_found = False
                for label in card.labels:
                    if label.id in [label.id for label in release_labels]:
                        label_found = True
                if label_found:
                    status = self.get_card_status(board, release, card)
                    features.append(
                        TrelloFeature(
                            board=board.name,
                            name=card.name,
                            release=release,
                            status=status,
                        )
                    )
        return features
