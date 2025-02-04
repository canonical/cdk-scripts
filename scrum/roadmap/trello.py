import datetime

from roadmap.logging import Logger


class TrelloBoard:
    STORY_POINTS_FIELD = "sp"
    EPIC_POINTS = 1000
    EPIC_LABEL_COLOR = "sky"
    EPIC_LABEL_NAME = "Epic"
    STALE_LABEL_NAME = "Stale"
    STALE_LABEL_COLOR = "yellow"
    FEEDBACK_LABEL_COLOR = "purple"
    FEEDBACK_LABEL_NAME = "feedback"
    LISTS = []

    def __init__(self, client, name=None, short_id=None):
        if not name and not id:
            raise ValueError("Either a board name or short_id must be provided")
        self.short_id = short_id
        self.id = None
        self.name = name
        self._client = client
        self._lists = None
        self._labels = None
        self._cards = None
        self._visible_cards = None
        self._custom_fields = None
        self._epics = []
        self._epic_label = None
        self._stale_label = None
        self._feedback_label = None
        self.logger = Logger()

    @property
    def _board(self):
        if self.short_id:
            board = self._client.get_board(self.short_id)
            self.name = board.name
            self.id = board.id
            return board

        all_boards = self._client.list_boards()
        for board in all_boards:
            if board.name.lower() == self.name.lower():
                self.id = board.id
                return board
        raise ValueError(f"Board {self.name} not in {all_boards}")

    @property
    def stale_label(self):
        if self._stale_label:
            return self._stale_label
        try:
            self._stale_label = next(
                filter(
                    lambda x: x.name == self.STALE_LABEL_NAME
                    and x.color == self.STALE_LABEL_COLOR,
                    self.labels,
                )
            )
        except StopIteration:
            raise ValueError(
                f"Label {self.STALE_LABEL_NAME}" f" not found on {self._board.name}."
            )

        return self._stale_label

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
    def epics(self):
        """Return all cards with the epic label"""
        if self._epics:
            return self._epics
        self._epics = []
        for card in self.visible_cards:
            try:
                next(filter(lambda x: x.name == self.epic_label.name, card.labels))
                self._epics.append(card)
            except (StopIteration, TypeError):
                # No epic labels or no labels at all
                pass
        return self._epics

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

    def _clear_card_cache(self):
        """Clear caches"""
        self._visible_cards = None
        self._cards = None
        self._epics = None

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

    def setup_board(self):
        # Add epic label
        try:
            epic_label = self.epic_label  # noqa: F841
        except ValueError:
            self._board.add_label(self.EPIC_LABEL_NAME, self.EPIC_LABEL_COLOR)
            self._labels = None  # clear cache

        # Add stale label
        try:
            stale_label = self.stale_label  # noqa: F841
        except ValueError:
            self._board.add_label(self.STALE_LABEL_NAME, self.STALE_LABEL_COLOR)
            self._labels = None  # clear cache

        # Add feedback label
        try:
            feedback_label = self.feedback_label  # noqa: F841
        except StopIteration:
            self._board.add_label(self.FEEDBACK_LABEL_NAME, self.FEEDBACK_LABEL_COLOR)
            self._labels = None  # clear cache

        # Add any lists in self.LISTS
        new_list = False
        for list in self.LISTS:
            try:
                next(filter(lambda x: x.name == list, self.lists))
            except StopIteration:
                self._board.add_list(list)
                new_list = True
        if new_list:
            self._lists = None  # clear cache

    def get_stale_cards(self, lists, delta=datetime.timedelta(days=10)):
        stale_cards = []
        now = datetime.datetime.now(datetime.timezone.utc)
        for card in self.visible_cards:
            for list in self.lists:
                if list.id == card.list_id:
                    list_name = list.name
            if list_name not in lists:
                # Only processes requetsed lists
                continue
            if now - card.date_last_activity > delta:
                self.logger.debug(f"Delta: {now - card.date_last_activity}")
                stale_cards.append(card)
        return stale_cards

    def label_stale_cards(self, lists, delta=datetime.timedelta(days=5)):
        stale_cards = self.get_stale_cards(lists, delta)
        for card in stale_cards:
            try:
                next(
                    filter(
                        lambda x: x.name == self.STALE_LABEL_NAME
                        and x.color == self.STALE_LABEL_COLOR,
                        card.labels,
                    )
                )
                # Already labeled
                self.logger.debug(f"Found existing lable, skipping {card.name}")
            except (StopIteration, TypeError):
                # No lables, or no stale label
                card.add_label(self.stale_label)
                self._clear_card_cache()
                self.logger.info(f"Labeling Stale Card: {card.name}")

    def update_sizes(self, sized_features=[]):
        """Update story point field from sized_features
        Sized Features will be updated as well as all epics on the board"""
        for feature in sized_features:
            if not feature.story_points:
                self.logger.warn(f"Features {feature.name} has no story points")
                continue
            try:
                card = next(
                    filter(lambda x: x.name == feature.name, self.visible_cards)
                )
            except StopIteration:
                # Feature doesn't have a card on this board
                continue
            if feature.story_points == self.EPIC_POINTS:
                # check label
                self.logger.debug(f"Checking epic: {feature.name}")
                if not card.labels or not len(
                    [
                        label
                        for label in card.labels
                        if label.name == self.EPIC_LABEL_NAME
                        and label.color == self.EPIC_LABEL_COLOR
                    ]
                ):
                    self.logger.debug(f"Labeling epic: {feature.name}")
                    card.add_label(self.epic_label)
                    self._clear_card_cache()
                # Zero score, calculated at the end
                card.set_custom_field(str(0), self.sp_field)
                self._clear_card_cache()
                continue
            card.set_custom_field(str(feature.story_points), self.sp_field)
        for card in self.epics:
            points = self._get_points(card)
            card.set_custom_field(str(points), self.sp_field)
            self._clear_card_cache()
        self._clear_card_cache()

    def _url_from_name(self, name):
        """Return the url for a card by name, if it is on this board"""
        self.logger.debug(f"Searching for card: {name}")
        for card in self.visible_cards:
            if card.name == name:
                self.logger.debug(f"Found card: {name}")
                return card.url
        self.logger.debug(f"No url for card name: {name}")
        self.logger.debug(f"Names: {[c.name for c in self.visible_cards]}")
        return None

    def update_features(self, features, new_list=None):
        """Update features on this board, if new_list is provided add new cards to that
        list, otherwise skip new cards"""
        card_names = [card.name for card in self.visible_cards]
        for feature in features:
            self.logger.debug(f"Checking feature for import: {feature.name}")
            if feature.name not in card_names:
                # New card
                if not new_list:
                    self.logger.debug(f"Skipping feature, not on board: {feature.name}")
                    continue
                nlist = [lst for lst in self.lists if lst.name == new_list][0]
                self.logger.debug(f"Creating card in list: {nlist}")
                card = nlist.add_card(name=feature.name, desc=feature.description)
                self._clear_card_cache()
                for attachment in feature.attachments:
                    self.logger.debug(f"Checking Attachment: {attachment}")
                    if attachment.name:
                        self.logger.debug(f"Searching for card: {attachment.name}")
                        url = self._url_from_name(attachment.name)
                        if url:
                            self.logger.debug(f"Found card: {attachment.name}")
                            card.attach(url=url)
                            self._clear_card_cache()
                    elif attachment.url:
                        self.logger.debug(f"Attaching: {attachment.url}")
                        card.attach(url=attachment.url)
                        self._clear_card_cache()
            else:
                # Existing card
                card = [
                    card for card in self.visible_cards if card.name == feature.name
                ][0]
                if card.description != feature.description:
                    self.logger.debug(f"Updating description on: {card.name}")
                    card.set_description(feature.description)
                    self._clear_card_cache()
                if feature.attachments:
                    self.logger.debug(f"Checking attachments: {feature.name}")
                    existing = card.attachments
                    for attachment in feature.attachments:
                        if attachment.name:
                            url = self._url_from_name(attachment.name)
                        else:
                            url = attachment.url
                        if url and url not in [a["url"] for a in existing]:
                            self.logger.debug(f"Attaching {url} to {card.name}")
                            card.attach(url=url)
                            self._clear_card_cache()

    def add_card(self, name, description, list, points=0):
        """Add a card from name, descriptoin, and list."""
        self.logger.debug(f"Searching for list: {list}")
        nlist = [lst for lst in self.lists if lst.name == list][0]
        self.logger.debug(f"Creating card in list: {nlist}")
        card = nlist.add_card(name=name, desc=description)
        if points:
            card.set_custom_field(str(points), self.STORY_POINTS_FIELD)
        self._clear_card_cache()

    def _get_points(self, card, skip_cards=None, depth=1):
        """Recursively sum story points for card"""
        if not skip_cards:
            skip_cards = []
        points = 0
        currnet_depth = 1
        for field in card.custom_fields:
            if field.name == self.STORY_POINTS_FIELD:
                points = int(field.value)
        self.logger.debug(f"Getting points for: {card.name}")
        self.logger.debug(f"skip_cards: {skip_cards}")
        subpoints_list = []
        if not currnet_depth > depth:
            # Process attachments
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
                        filter(lambda x: x.url == attachment.url, self.visible_cards)
                    )
                except StopIteration:
                    # Card not found on this board
                    self.logger.debug(
                        f"Attachment not card on this board board: {attachment.url}"
                    )
                    continue
                skip_cards.append(card.url)
                new_depth = depth - 1
                subpoints = self._get_points(
                    subcard, skip_cards=skip_cards, depth=new_depth
                )
                self.logger.debug(f"Subpoints for {card.name}: {subpoints}")
                subpoints_list.append(subpoints)
        self.logger.debug(f"Found points for: {card.name}")
        if subpoints_list:
            self.logger.debug(
                f"Returning point results: subpoints: {sum(subpoints_list, points)}"
            )
            return sum(subpoints_list, points)
        else:
            self.logger.debug(f"Returning point results: {points}")
            return points

    def get_features(self, visible=True, attachments=False, skip=None):
        features = []
        self.logger.debug(f"Getting features skip: {skip}")
        if visible:
            if skip:
                cards = []
                skip_ids = []
                for list in self.lists:
                    if list.name in skip:
                        skip_ids.append(list.id)
                        self.logger.info(f"Skipping list: {list.name}")
                for card in self.visible_cards:
                    if card.list_id not in skip_ids:
                        cards.append(card)
            else:
                cards = self.visible_cards
        else:
            cards = self.cards
        for card in cards:
            features.append(
                TrelloFeature(
                    card=card,
                    status=self._get_card_status(card),
                    sp_field=self.sp_field,
                    epic_name=self.EPIC_LABEL_NAME,
                    attachments=attachments,
                )
            )
        return features

    def _get_card_status(self, card):
        """Return a status for this card"""
        return "Undefined"


class TrelloFeature:
    def __init__(
        self, card, status, sp_field, release=None, epic_name="Epic", attachments=False
    ):
        self.name = card.name
        self.description = card.description
        self.status = status
        self.links = []
        self.attachments = []
        self.release = release
        self.story_points = None
        self._set_story_points(card, sp_field)
        self.labels = card.labels or []
        self.closed = card.closed
        self.epic = False
        self._check_epic(card, epic_name)
        if attachments:
            self._set_attachments(card)

    def _check_epic(self, card, epic_name):
        if not card.labels:
            return
        for label in card.labels:
            if label.name == epic_name:
                self.epic = True
                return

    def _set_attachments(self, card):
        for attachment in card.get_attachments():
            if attachment.url:
                self.links.append(attachment.url)
            self.attachments.append(attachment)

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
            self._clear_card_cache()

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
                self._clear_card_cache()

    def add_feature_cards(self, features, update_description=False, update_links=True):
        """Add missing cards"""
        card_names = [card.name for card in self.visible_cards]
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
                if feature.epic:
                    list_name = "Epic"
                elif feature.story_points:
                    list_name = f"Size {feature.story_points}"
                else:
                    list_name = f"Unsized"
                self.logger.debug(f"Feature Size: {feature.story_points}")
                slist = [lst for lst in self.lists if lst.name == list_name][0]
                self.logger.debug(f"Found List: {slist}")
                labels = []
                for label in feature.labels:
                    if label.name == self.feedback_label.name:
                        labels = [self.feedback_label]
                        break
                card = slist.add_card(
                    name=feature.name,
                    desc=feature.description,
                    labels=labels,
                )
                self._clear_card_cache
                for link in feature.links:
                    card.attach(url=link)
                    self._clear_card_cache()
            elif update_description or update_links:
                # Existing card
                card = [
                    card for card in self.visible_cards if card.name == feature.name
                ][0]
                if update_description and card.description != feature.description:
                    card.set_description(feature.description)
                    self._clear_card_cache()
                if update_links and feature.links:
                    attachments = card.attachments
                    for link in feature.links:
                        if link not in [a["url"] for a in attachments]:
                            card.attach(url=link)
                            self._clear_card_cache()

    def get_features(self, *args, **kwargs):
        for list in sorted(self.lists, key=lambda x: x.name, reverse=True):
            if list.name == "Unsized":
                continue
            if list.name == "Epic":
                points = self.EPIC_POINTS
            else:
                points = list.name.split(" ")[1]
            for card in list.list_cards_iter():
                self.logger.debug(f"Setting {self.sp_field} to {points} on {card.name}")
                card.set_custom_field(str(points), self.sp_field)
                self._clear_card_cache()
                for attachment in card.get_attachments():
                    if attachment.url.startswith("https://trello.com"):
                        self.logger.debug(f"Checking for card: {attachment}")
                        for subcard in self.visible_cards:
                            if subcard.url == attachment.url:
                                self.logger.debug(f"Adding name: {subcard.name}")
                                card.remove_attachment(attachment.id)
                                card.attach(name=subcard.name, url=subcard.url)
                                self._clear_card_cache()
        return super().get_features(*args, **kwargs)


class BacklogBoard(TrelloBoard):
    FEEDBACK_LIST = "Product Feedback"
    LISTS = [
        "Misc",
        FEEDBACK_LIST,
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._feedback_list = None

    @property
    def feedback_list(self):
        if self._feedback_list:
            return self._feedback_list
        self._feedback_list = [
            lst for lst in self.lists if lst.name == self.FEEDBACK_LIST
        ][0]
        return self._feedback_list

    def add_feedback_cards(
        self, product_feedback, update_description=False, update_bugs=True
    ):
        """Add missing cards"""
        card_names = [card.name for card in self.visible_cards]
        for feedback in product_feedback:
            self.logger.debug(f"Checking feedback: {feedback.name}")
            if feedback.name not in card_names:
                # New card
                self.logger.debug(f"Creating Card: {feedback.name}")
                card = self.feedback_list.add_card(
                    name=feedback.name,
                    desc=feedback.description,
                    labels=[self.feedback_label],
                )
                for bug in feedback.bugs:
                    card.attach(url=bug)
                    self._clear_card_cache()
                if feedback.story_points:
                    card.set_custom_field(str(feedback.story_points), self.sp_field)
            elif update_description or update_bugs:
                # Existing card
                card = [
                    card for card in self.visible_cards if card.name == feedback.name
                ][0]
                if update_description and card.description != feedback.description:
                    card.set_description(feedback.description)
                    self._clear_card_cache()
                if update_bugs and feedback.bugs:
                    attachments = card.attachments
                    for bug in feedback.bugs:
                        if bug not in [a["url"] for a in attachments]:
                            card.attach(url=bug)
                            self._clear_card_cache()
        self._clear_card_cache()

    def setup_board(self):
        super().setup_board()
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
    REVIEW_LIST = "In Review"
    LISTS = [REVIEW_LIST]
    RELEASE_COLORS = ["green", "blue", "orange", "red", "black"]

    def __init__(self, *args, product_categories=[], **kwargs):
        super().__init__(*args, **kwargs)
        self.product_categories = product_categories

    def setup_board(self):
        super().setup_board()

    def add_pull(self, pulls):
        """Create a card to review a pull request"""
        lst = [lst for lst in self.lists if lst.name == self.REVIEW_LIST][0]
        existing_cards = [card for card in lst.list_cards()]
        existing_urls = []
        for card in existing_cards:
            for attachment in card.attachments:
                url = attachment.get("url", "")
                if "/pull/" in url:
                    self.logger.debug(f"Found existing PR: {url} on {card.name}")
                    existing_urls.append(url)
        for pull in pulls:
            self.logger.debug(f"Adding card for {pull.url}")
            name = f'PR Review {pull.url.split("/")[-3]} #{pull.number}'
            desc = f"""{pull.reason}
                    Url: {pull.url}
                    {pull.body}"""
            if name in [card.name for card in existing_cards]:
                self.logger.debug(f"Skipping, card already exists: {name}")
                continue
            elif pull.url in existing_urls:
                self.logger.debug(f"Skipping, url already exists: {pull.url}")
                continue
            self.logger.info(f"Added card for: {pull.url}")
            card = lst.add_card(name=name, desc=desc, position="bottom")
            card.attach(url=pull.url)
        self._clear_card_cache()

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
        card_names = [card.name for card in self.visible_cards]
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
            self._clear_card_cache()

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
            for card in self.visible_cards:
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
                    self._claer_card_cache()
                    break

    def label_stale_cards(self, lists=[], delta=datetime.timedelta(days=5)):
        if not lists:
            lists = self.IN_PROGRESS_LISTS
        super().label_stale_cards(lists, delta)

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
                        filter(lambda x: x.url == attachment.url, self.visible_cards)
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
