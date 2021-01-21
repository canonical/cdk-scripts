from roadmap.logging import Logger


class TrelloBoard:
    STORY_POINTS_FIELD = "sp"
    EPIC_POINTS = 1000
    EPIC_LABEL_COLOR = "sky"
    EPIC_LABEL_NAME = "Epic"

    def __init__(self, client, name=None, id=None):
        if not name and not id:
            raise ValueError("Either a board name or id must be provided")
        self.id = id
        self.name = name
        self._client = client
        self._lists = None
        self._labels = None
        self._cards = None
        self._visible_cards = None
        self._custom_fields = None
        self._epics = []
        self._epic_label = None
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
        """Card  retrevial options
        all = every card
        visible = cards that are not archived and on an list that isn't archived
        open = unarchived cards on archived lists
        """
        if self._cards:
            return self._cards
        self._cards = self._board.all_cards()
        return self._cards

    @property
    def visible_cards(self):
        if self._visible_cards:
            return self._visible_cards
        self._visible_cards = self._board.visible_cards()
        return self._visible_cards

    @property
    def custom_fields(self):
        if self._custom_fields:
            return self._custom_fields
        self._custom_fields = self._board.get_custom_field_definitions()
        return self._custom_fields

    @property
    def sp_field(self):
        """Return the custom story point field"""
        try:
            sp = next(
                filter(lambda x: x.name == self.STORY_POINTS_FIELD, self.custom_fields)
            )
        except StopIteration:
            raise ValueError(
                f"Custom Field {self.STORY_POINTS_FIELD}"
                f" not found on {self._board.name}."
            )
        return sp

    @property
    def epic_label(self):
        if self._epic_label:
            return self._epic_label
        try:
            self._epic_label = next(
                filter(
                    lambda x: x.name == self.EPIC_LABEL_NAME
                    and x.color == self.EPIC_LABEL_COLOR,
                    self.labels,
                )
            )
        except StopIteration:
            raise ValueError(
                f"Label {self.EPIC_LABEL_NAME}" f" not found on {self._board.name}."
            )

        return self._epic_label

    @property
    def epics(self):
        """Return all cards with the epic label"""
        if self._epics:
            return self._epics
        self._epics = []
        for card in self.cards:
            try:
                next(filter(lambda x: x.name == self.epic_label.name, card.labels))
                self._epics.append(card)
            except (StopIteration, TypeError):
                # No epic labels or no labels at all
                pass
        return self._epics

    def setup_board(self):
        try:
            epic_label = self.epic_label  # noqa: F841
        except ValueError:
            self._board.add_label(self.EPIC_LABEL_NAME, self.EPIC_LABEL_COLOR)
            self._labels = None  # clear cache

    def update_sizes(self, sized_features=[]):
        """Update story point field from sized_features
        Sized Features will be updated as well as all epics on the board"""
        for feature in sized_features:
            if not feature.story_points:
                self.logger.warn(f"Features {feature.name} has no story points")
                continue
            try:
                card = next(filter(lambda x: x.name == feature.name, self.cards))
            except StopIteration:
                # Feature doesn't have a card on this board
                continue
            if feature.story_points == self.EPIC_POINTS:
                # check label
                if not len(
                    [
                        label
                        for label in card.labels
                        if label.name == self.EPIC_LABEL_NAME
                        and label.color == self.EPIC_LABEL_COLOR
                    ]
                ):
                    card.add_label(self.epic_label)
                # Zero score, calculated at the end
                card.set_custom_field(str(0), self.sp_field)
                continue
            self.logger.debug(f"{type(feature.story_points)}")
            card.set_custom_field(str(feature.story_points), self.sp_field)
        self._cards = None
        self._epics = None
        for card in self.epics:
            points = self._get_points(card)
            card.set_custom_field(str(points), self.sp_field)
        self._cards = None
        self._epics = None

    def _get_points(self, card, skip_cards=[]):
        """Recursively sum story points for card"""
        points = 0
        for field in card.custom_fields:
            if field.name == self.STORY_POINTS_FIELD:
                points = int(field.value)
        subpoints_list = []
        for attachment in card.get_attachments():
            if attachment.is_upload:
                self.logger.debug(f"Skipping upload")
                continue
            if attachment.url in skip_cards:
                self.logger.debug(f"Skipping skip_card: {attachment.url}")
                continue
            self.logger.debug(f"Searching: {attachment.url}")
            try:
                subcard = next(filter(lambda x: x.url == attachment.url, self.cards))
            except StopIteration:
                # Card not found on this board
                self.logger.debug(
                    f"Attachment not card on this board board: {attachment.url}"
                )
                continue
            skip_cards.append(card.url)
            subpoints = self._get_points(subcard, skip_cards=skip_cards)
            self.logger.debug(f"Subpoints: {subpoints}")
            subpoints_list.append(subpoints)
        if subpoints_list:
            return sum(subpoints_list, points)
        else:
            return points

    def get_features(self, visible=True, attachments=False):
        features = []
        if visible:
            cards = self.visible_cards
        else:
            cards = self.cards
        for card in cards:
            features.append(
                TrelloFeature(
                    card=card,
                    status=self._get_card_status(card),
                    sp_field=self.sp_field,
                    attachments=attachments,
                )
            )
        return features

    def _get_card_status(self, card):
        """Return a status for this card"""
        return "Undefined"


class TrelloFeature:
    def __init__(self, card, status, sp_field, release=None, attachments=False):
        self.name = card.name
        self.description = card.description
        self.status = status
        self.links = []
        self.release = release
        self.story_points = None
        self._set_story_points(card, sp_field)
        self.closed = card.closed
        if attachments:
            self._set_attachments(card)

    def _set_attachments(self, card):
        for attachment in card.get_attachments():
            if attachment.url:
                self.links.append(attachment.url)

    def _set_story_points(self, card, sp_field):
        for field in card.custom_fields:
            if field.name == sp_field.name:
                self.story_points = int(field.value)

    def __repr__(self):
        return f"'{self.name}':{self.story_points}:{self.status}"


class SizingBoard(TrelloBoard):
    def __init__(self, *args, sizes=[1, 2, 3, 5, 8, 13, 21], **kwargs):
        super().__init__(*args, **kwargs)
        self._sizes = sizes

    def setup_board(self):
        super().setup_board()
        self.setup_lists()

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

    def truncate_lists(self, len=3):
        """Truncate size lists to max len"""
        for list in self.lists:
            if list.name == "Unsized":
                # Don't truncate the unsized list
                continue
            self.logger.debug(f"Truncating {list} to {len} cards")
            for i, card in enumerate(list.list_cards_iter()):
                if i < len:
                    continue
                card.delete()

    def add_feature_cards(self, features, update_description=False, update_links=True):
        """Add missing cards"""
        card_names = [card.name for card in self.cards]
        for feature in features:
            try:
                if feature.status.state == feature.status.DONE:
                    # Don't add completed scrum cards
                    continue
            except AttributeError:
                # No Scrum Status to check
                pass
            if feature.name not in card_names:
                # New card
                if feature.story_points:
                    if feature.story_points not in self._sizes:
                        list_name = "Epic"
                    else:
                        list_name = f"Size {feature.story_points}"
                else:
                    list_name = f"Unsized"
                slist = [lst for lst in self.lists if lst.name == list_name][0]
                self.logger.debug(f"Feature Size: {feature.story_points}")
                self.logger.debug(f"Found List: {slist}")
                card = slist.add_card(name=feature.name, desc=feature.description)
                for link in feature.links:
                    card.attach(url=link)
            elif update_description or update_links:
                # Existing card
                card = [card for card in self.cards if card.name == feature.name][0]
                if update_description and card.description != feature.description:
                    card.set_description(feature.description)
                if update_links and feature.links:
                    attachments = card.attachments
                    for link in feature.links:
                        if link not in [a["url"] for a in attachments]:
                            card.attach(url=link)


class BacklogBoard(TrelloBoard):
    FEEDBACK_LIST = "Product Feedback"
    FEEDBACK_LABEL_COLOR = "purple"
    FEEDBACK_LABEL_NAME = "feedback"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._feedback_list = None
        self._feedback_label = None

    @property
    def feedback_list(self):
        if self._feedback_list:
            return self._feedback_list
        self._feedback_list = [
            lst for lst in self.lists if lst.name == self.FEEDBACK_LIST
        ][0]
        return self._feedback_list

    @property
    def feedback_label(self):
        if self._feedback_label:
            return self._feedback_label
        self._feedback_label = next(
            filter(
                lambda x: x.name == self.FEEDBACK_LABEL_NAME
                and x.color == self.FEEDBACK_LABEL_COLOR,
                self.labels,
            )
        )
        return self._feedback_label

    def add_feedback_cards(
        self, product_feedback, update_description=False, update_bugs=True
    ):
        """Add missing cards"""
        card_names = [card.name for card in self.cards]
        for feedback in product_feedback:
            if feedback.name not in card_names:
                # New card
                card = self.feedback_list.add_card(
                    name=feedback.name,
                    desc=feedback.description,
                    labels=[self.feedback_label],
                )
                for bug in feedback.bugs:
                    card.attach(url=bug)
                if feedback.story_points:
                    card.set_custom_field(str(feedback.story_points), self.sp_field)
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
        self._cards = None  # Clear cache

    def setup_board(self):
        super().setup_board()
        try:
            feedback_list = self.feedback_list  # noqa: F841
        except IndexError:
            self._board.add_list(self.FEEDBACK_LIST)
            self._lists = None  # clear cache

        try:
            feedback_label = self.feedback_label  # noqa: F841
        except StopIteration:
            self._board.add_label(self.FEEDBACK_LABEL_NAME, self.FEEDBACK_LABEL_COLOR)
            self._labels = None  # clear cache


class ScrumBoard(TrelloBoard):
    IN_PROGRESS_LISTS = [
        "In Progress",
        "In Review",
        "Blocked",
        "Under review",
        "Review",
    ]
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

    def get_release_features(self, release, visible=True):
        release_labels = filter(
            lambda x: x.name == release and x.color in self.RELEASE_COLORS, self.labels
        )
        release_ids = [lbl.id for lbl in release_labels]
        if visible:
            cards = self._board.visible_cards()
        else:
            cards = self.cards

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
            status = self._get_card_status(card, release)
            features.append(
                TrelloFeature(
                    card=card, status=status, sp_field=self.sp_field, release=release
                )
            )
        return features

    def _get_card_status(self, card, release=None, skip_cards=[]):
        lst = next(filter(lambda x: x.id == card.list_id, self.lists))
        status = ScrumStatus()
        if lst.name.lower().startswith("done"):
            status.done()
        elif lst.name in self.IN_PROGRESS_LISTS:
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
                if not attachment.url:
                    self.logger.debug(f"Skipping no url")
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
                        f"Attachment not card on this board: {attachment.url}"
                    )
                    continue
                skip_cards.append(card.url)
                substatus = self._get_card_status(
                    subcard, release=release, skip_cards=skip_cards
                )
                self.logger.debug(f"SubStatus: {substatus}")
                if substatus != substatus.NOT_STARTED:
                    status.started()
        if release:
            try:
                label = next(filter(lambda x: x.name == release, card.labels))
                status.set_color(label.color)
            except TypeError:
                # Don't set color if there is no release label
                self.logger.debug(f"Not setting color on status: {card.name}")
        return status


class ScrumStatus:
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
