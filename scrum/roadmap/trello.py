from functools import lru_cache

# from roadmap.feature import TrelloFeature
from roadmap.logging import Logger

# from trello import TrelloClient

cache = lru_cache(maxsize=None)


class TrelloBoard:
    STORY_POINTS_FIELD = "sp"

    def __init__(self, client, name=None, id=None):
        if not name and not id:
            raise ValueError("Either a board name or id must be provided")
        self.id = id
        self.name = name
        self._client = client
        self._lists = None
        self._labels = None
        self._cards = None
        self._custom_fields = None
        self.logger = Logger()

    @property
    def _board(self):
        if self.id:
            board = self._client.get_board(self.id)
            self.name = board.name
            return board

        all_boards = self._client.list_boards()
        for board in all_boards:
            if board.name.lower() == self.name.lower():
                self.id = board.id
                return board
        raise ValueError(f"Board {self.name} not in {all_boards}")

    @property
    def lists(self):
        if self._lists:
            return self._lists
        self._lists = self._board.all_lists()
        return self._lists

    @property
    def labels(self):
        if self._labels:
            return self._labels
        self._labels = self._board.get_labels(limit=100)
        return self._labels

    @property
    def cards(self):
        if self._cards:
            return self._cards
        self._cards = self._board.all_cards()
        return self._cards

    @property
    def custom_fields(self):
        if self._custom_fields:
            return self._custom_fields
        self._custom_fields = self._board.get_custom_field_definitions()
        return self._custom_fields

    def update_sizes(self, sized_features):
        """Update story point field from sized_features"""
        for feature in sized_features:
            if not feature.size:
                continue
            try:
                card = next(filter(lambda x: x.name == feature.name, self.cards))
            except StopIteration:
                # Feature doesn't have a card on this board
                continue
            try:
                sp = next(
                    filter(
                        lambda x: x.name == self.STORY_POINTS_FIELD, self.custom_fields
                    )
                )
            except StopIteration:
                raise ValueError(
                    f"Custom Field {self.STORY_POINTS_FIELD}"
                    " not found on {self.board.name}."
                )
            self.logger.debug(f"{type(feature.size)}")
            card.set_custom_field(feature.size, sp)

    # @property
    # def _card_names(self):
    #     all_cards = self._board.all_cards()
    #     card_names = [card.name for card in all_cards]
    #     return card_names


class SizingBoard(TrelloBoard):
    def __init__(self, *args, sizes=[1, 2, 3, 5, 8, 13, 21], **kwargs):
        super().__init__(*args, **kwargs)
        self._sizes = sizes

    def setup_lists(self):
        all_lists = self._board.all_lists()
        list_names = [list.name for list in all_lists]
        desired_lists = ["Unsized"]
        desired_lists.extend([f"Size {n}" for n in self._sizes])
        desired_lists.append("Epic")
        missing_lists = [name for name in desired_lists if name not in list_names]
        for name in missing_lists:
            self._board.add_list(name, pos="bottom")
        self._lists = None

    def clear_board(self):
        for card in self.cards:
            card.delete()

    def add_feedback_cards(
        self, product_feedback, update_description=False, update_bugs=True
    ):
        """Add missing cards"""
        card_names = [card.name for card in self.cards]
        for feedback in product_feedback:
            if feedback.name not in card_names:
                # New card
                if feedback.story_points:
                    if feedback.story_points not in self._sizes:
                        list_name = "Epic"
                    else:
                        list_name = f"Size {feedback.story_points}"
                else:
                    list_name = f"Unsized"
                slist = [lst for lst in self.lists if lst.name == list_name][0]
                self.logger.debug(f"Feature Size: {feedback.story_points}")
                self.logger.debug(f"Found List: {slist}")
                card = slist.add_card(name=feedback.name, desc=feedback.description)
                for bug in feedback.bugs:
                    card.attach(url=bug)
            elif update_description or update_bugs:
                # Existing card
                card = [card for card in self.cards if card.name == feedback.name][0]
                if update_description and card.description != feedback.description:
                    card.set_description(feedback.description)
                if update_bugs and feedback.bugs:
                    attachments = card.attachments
                    for bug in feedback.bugs:
                        if bug not in [a["url"] for a in attachments]:
                            card.attach(url=bug)

    def add_team_cards(self, team_features):
        """Add cards from team feautres"""
        # Team features have all the fields of a Product feature if links are treated
        # like bugs. For now we'll do the mapping.
        for feature in team_features:
            feature.bugs = feature.links
        self.add_feedback_cards(team_features)

    @property
    def sized_features(self):
        sized_features = []
        for card in self.cards:
            lst = [lst for lst in self.lists if card.list_id == lst.id][0]
            if "Epic" in lst.name:
                # TODO: Sum up size of all attached cards
                continue
            size = lst.name.lstrip("Size").strip()
            try:
                size = int(size)
            except ValueError:
                size = None
            self.logger.debug(f"Size: {size}")
            sized_features.append(SizedFeature(name=card.name, size=size))
        return sized_features


class SizedFeature:
    def __init__(self, name, size):
        self.name = name
        try:
            self.size = int(size)
        except TypeError:
            self.size = None

    def __repr__(self):
        return f"{self.name}:{self.size}"


class TeamBoard(TrelloBoard):
    STORY_POINTS_FIELD = "sp"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_features(self, only_visible=True):
        features = []
        for card in self.cards:
            if only_visible and not card.closed:
                features.append(TeamFeature(card=card))
        return features

    # def update_sizes(self, sized_features):
    #     for feature in sized_features:
    #         try:
    #             card = next(filter(lambda x: x.name == feature.name, self.cards))
    #         except StopIteration:
    #             # Feature doesn't have a card on this board
    #             continue
    #         try:
    #             sp = next(
    #                 filter(
    #                     lambda x: x.name == self.STORY_POINTS_FIELD, self.custom_fields  # noqa
    #                 )
    #             )
    #         except StopIteration:
    #             raise ValueError(
    #                 f"Custom Field {self.STORY_POINTS_FIELD}"
    #                 " not found on {self.board.name}."
    #             )
    #         card.set_custom_field(str(feature.size), sp)


class TeamFeature:
    def __init__(self, card):
        self.name = card.name
        self.description = card.description
        self.links = []
        # TODO Check for a custom_field for story points
        self.story_points = None
        for attachment in card.get_attachments():
            if attachment.url:
                self.links.append(attachment.url)


class ScrumBoard(TrelloBoard):
    IN_PROGRESS_LIST = "In Progress"
    DONE_LIST = "Done"
    RELEASE_COLORS = ["green", "blue", "orange", "red", "black"]

    def __init__(self, *args, product_categories=[], **kwargs):
        super().__init__(*args, **kwargs)
        self.product_categories = product_categories

    def create_release(self, release):
        """Create A new release list"""
        pos = None
        all_lists = self._board.all_lists()
        list_present = False
        for lst in all_lists:
            if release == lst.name:
                list_present = True
        if not list_present:
            for lst in all_lists:
                if self.IN_PROGRESS_LIST.lower() == lst.name.lower():
                    pos = lst.pos - 1
                    break
            self._board.add_list(release, pos)
            self._lists = None  # Clear cache

        for color in self.RELEASE_COLORS:
            self._board.add_label(release, color)
        self._labels = None  # Clear cache

    def create_cards(self, roadmap_features):
        """Create cards for a list of roadmap features"""
        card_names = [card.name for card in self.cards]
        self.logger.info("Creating roadmap cards")
        for feature in roadmap_features:
            if feature.category not in self.product_categories:
                self.logger.debug(
                    f"{self.name} not adding {feature}, category does not match"
                )
                continue
            if feature.name in card_names:
                # Card already exists
                self.logger.debug(
                    f"{self.name} not adding {feature}, card already exists"
                )
                continue
            lst = [lst for lst in self.lists if lst.name == feature.release][0]
            label = [
                label
                for label in self.labels
                if label.name == feature.release and label.color == "green"
            ][0]
            self.logger.debug(f"Adding card {feature.name}")
            lst.add_card(name=feature.name, labels=[label], position="bottom")
            self._cards = None  # Clear card cache

    def tag_release(self, features):
        """Add feature tags to existing cards"""
        self.logger.info("Tagging existing cards with relese")
        for feature in features:
            release_label = [
                label
                for label in self.labels
                if label.name == feature.release and label.color == "green"
            ][0]
            self.logger.debug(f"Looking for feature {feature.name}")
            for card in self.cards:
                if card.name == feature.name:
                    self.logger.debug(f"Found card {card.name}")
                    try:
                        next(
                            filter(lambda x: x.name == release_label.name, card.labels)
                        )
                        # Already labeled
                        self.logger.debug(f"Found existing lable, skipping {card.name}")
                        break
                    except (StopIteration, TypeError):
                        # No lables, or no release label
                        pass
                    self.logger.debug(f"Labeling card {card.name}")
                    card.add_label(release_label)
                    break

    def get_release_features(self, release, only_visible=True):
        release_labels = filter(
            lambda x: x.name == release and x.color in self.RELEASE_COLORS, self.labels
        )
        release_ids = [lbl.id for lbl in release_labels]
        if only_visible:
            cards = self._board.visible_cards()
        else:
            cards = self._board.all_cards()

        features = []
        for card in cards:
            if not card.labels:
                continue
            in_release = False
            for label in card.labels:
                if label.id in release_ids:
                    in_release = True
            if not in_release:
                continue
            status = self.get_card_status(card, release)
            features.append(ScrumFeature(card=card, status=status, release=release))
        return features

    def get_card_status(self, card, release, skip_cards=[]):
        lst = next(filter(lambda x: x.id == card.list_id, self.lists))
        status = FeatureStatus()
        if lst.name == self.DONE_LIST:
            status.done()
        elif lst.name != release:
            status.started()
        else:
            # Set started if checklist has completed items
            for chklst in card.checklists:
                for item in chklst.items:
                    if item["checked"]:
                        status.started()
            # Set started if an attached card *on this board* has started
            for attachment in card.get_attachments():
                if attachment.is_upload:
                    self.logger.debug(f"Skipping upload")
                    continue
                if attachment.url in skip_cards:
                    self.logger.debug(f"Skipping skip_card: {attachment.url}")
                    continue
                self.logger.debug(f"Searching: {attachment.url}")
                try:
                    subcard = next(
                        filter(lambda x: x.url == attachment.url, self.cards)
                    )
                except StopIteration:
                    # Card not found on this board
                    self.logger.debug(
                        f"Attachment not card on this board board: {attachment.url}"
                    )
                    continue
                substatus = self.get_card_status(
                    subcard, release, skip_cards=skip_cards.append(card.url)
                )
                self.logger.debug(f"SubStatus: {substatus}")
                if substatus != substatus.NOT_STARTED:
                    status.started()
        try:
            label = next(filter(lambda x: x.name == release, card.labels))
            status.set_color(label.color)
        except TypeError:
            # Don't set color if there is no release label
            self.logger.debug(f"Not setting color on status: {card.name}")
            pass
        return status


class ScrumFeature:
    def __init__(self, card, status, release=None):
        self.name = card.name
        self.status = status
        self.release = release


class FeatureStatus:
    NOT_STARTED = 1
    IN_PROGRESS = 2
    DONE = 3

    def __init__(self):
        self._color = "white"
        self._state = self.NOT_STARTED

    @property
    def color(self):
        return self._color

    @property
    def state(self):
        return self._state

    def set_color(self, color):
        self._color = color.lower()

    def not_started(self):
        self._state = self.NOT_STARTED

    def started(self):
        self._state = self.IN_PROGRESS

    def done(self):
        self._state = self.DONE

    def __repr__(self):
        return f"{self.state}:{self.color}"


# class Utils:
#     def __init__(self, api_key, api_secret, boards):
#         self.client = TrelloClient(api_key, api_secret)
#         self.board_names = boards
#         self.logger = Logger()
#
#     @property
#     def boards(self):
#         all_boards = self.client.list_boards()
#         return filter(lambda x: x.name in self.board_names, all_boards)
#
#     def create_release(self, release):
#         """Create A new release list on all boards"""
#         for board in self.boards:
#             pos = None
#             all_lists = board.all_lists()
#             for card_list in all_lists:
#                 if release == card_list.name:
#                     return
#             for card_list in all_lists:
#                 if "In progress".lower() == card_list.name.lower():
#                     pos = card_list.pos - 1
#                     break
#             board.add_list(release, pos)
#             board.add_label(release, "green")
#             board.add_label(release, "blue")
#             board.add_label(release, "red")
#             board.add_label(release, "black")
#             board.add_label(release, "orange")
#
#     def create_feature_cards(self, roadmap_features, category_mapping):
#         """Create cards for a list of roadmap features"""
#         boards = list(self.boards)
#         for feature in roadmap_features:
#             board = next(
#                 filter(lambda x: x.name == category_mapping[feature.category], boards)
#             )
#             if self.get_card(board=board, name=feature.name, label_txt=feature.release):  # noqa
#                 # Card already exists
#                 continue
#             card_list = self.get_list_by_name(board, feature.release)
#             label = self.get_label(board, name=feature.release, color="green")
#             card_list.add_card(name=feature.name, labels=[label], position="bottom")
#
#     def get_card(self, board, name, label=None, label_txt=None):
#         cards = board.get_cards()
#         for card in cards:
#             if card.name == name:
#                 if label or label_txt:
#                     label_found = False
#                     for clabel in card.labels:
#                         if label and clabel.id == label.id:
#                             label_found = True
#                         if label_txt and clabel.name == label_txt:
#                             label_found = True
#                     if not label_found:
#                         continue
#                 return card
#         return None
#
#     def get_label(self, board, name, color):
#         """Return a label by name"""
#         for label in board.get_labels():
#             if label.name == name and label.color == color:
#                 return label
#         return None
#
#     def get_list_by_name(self, board, name):
#         """Return a list from a board by name"""
#         for list in board.all_lists():
#             if list.name.lower() == name.lower():
#                 return list
#         return None
#
#     def get_blackhole(self):
#         all_boards = self.client.list_boards()
#         for board in all_boards:
#             if board.name == "Blackhole":
#                 return board
#
#     def blackhole_lists(self, list_name):
#         boards = list(self.boards)
#         blackhole = self.get_blackhole()
#         for board in boards:
#             while True:
#                 victom = self.get_list_by_name(board, list_name)
#                 if victom:
#                     victom.move_to_board(blackhole)
#                 else:
#                     break
#
#     def delete_all_cards(self, list_name):
#         boards = list(self.boards)
#         for board in boards:
#             target_list = self.get_list_by_name(board, list_name)
#             if target_list:
#                 cards = target_list.list_cards()
#                 for card in cards:
#                     card.delete()
#
#     def get_card_status(self, board, release, card):
#         card_list = board.get_list(card.list_id)
#         if card_list.name.lower() == "done":
#             done = True
#         else:
#             done = False
#         if card_list.name.lower() == release:
#             started = False
#         else:
#             started = True
#         for label in card.labels:
#             if label.name == release:
#                 planned = True
#                 at_risk = False
#                 miss = False
#                 dropped = False
#                 if label.color == "blue":
#                     planned = False
#                 elif label.color == "orange":
#                     at_risk = True
#                 elif label.color == "red":
#                     miss = True
#                 elif label.color == "black":
#                     dropped = True
#         return FeatureStatus(started, done, planned, at_risk, miss, dropped)
#
#     def get_feature_cards(self, release):
#         boards = list(self.boards)
#         features = []
#         for board in boards:
#             release_labels = []
#             for color in ["green", "blue", "orange", "red", "black"]:
#                 label = self.get_label(board, release, color)
#                 if label:
#                     release_labels.append(label)
#             for card in board.visible_cards():
#                 label_found = False
#                 for label in card.labels:
#                     if label.id in [label.id for label in release_labels]:
#                         label_found = True
#                 if label_found:
#                     status = self.get_card_status(board, release, card)
#                     features.append(
#                         TrelloFeature(
#                             board=board.name,
#                             name=card.name,
#                             release=release,
#                             status=status,
#                         )
#                     )
#         return features
