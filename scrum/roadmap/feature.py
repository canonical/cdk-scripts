import re

from roadmap.logging import Logger


class BaseFeature:
    def __init__(self, name, release, status=None):
        self.name = name
        self.release = release
        self.status = status

    def __repr__(self):
        return f"{self.release}:{self.name}:{self.status.value}"


class RoadmapFeature(BaseFeature):
    def __init__(self, category, team, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.category = category
        self.team = team

    def __repr__(self):
        return f"{self.team}:{self.release}:{self.name}"


class TrelloFeature():
    def __init__(self, card, sp_field=None, attachments=False):
        self.name = card.name
        self.description = card.description
        self.links = []
        self.story_points = None
        if sp_field:
            for field in card.custom_fields:
                if field.name == sp_field.name:
                    self.story_points = int(field.value)
        # TODO: consider combining Features and SizedFeature for a single class
        self.size = self.story_points

        if attachments:
            for attachment in card.get_attachments():
                if attachment.url:
                    self.links.append(attachment.url)

    def __repr__(self):
        return f"{self.release}:{self.name}:{self.status.value}"


class FeedbackFeature:
    RESOLVED_HEADER = "Resolved"
    DESCRIPTION_HEADER = "Description"
    TITLE_HEADER = "Title"
    STORY_POINTS_HEADER = "Duration"
    LAUNCHPAD_HEADER = "LP"

    def __init__(self, product, row):
        self.product = product
        self.logger = Logger()
        self._row = row
        self._lp_reg = re.compile(r"^\d{7}$")

    @property
    def name(self):
        title = self._row.get(self.TITLE_HEADER, "")
        if not len(title):
            title = self.description[:32]
        return title.strip()

    @property
    def description(self):
        return self._row.get(self.DESCRIPTION_HEADER, "").strip()

    @property
    def story_points(self):
        sp = self._row.get(self.STORY_POINTS_HEADER, None)
        if sp:
            sp = int(sp)
        return sp

    @property
    def resolved(self):
        resolved = self._row.get(self.RESOLVED_HEADER, False) == "TRUE"
        return resolved

    @property
    def bugs(self):
        links = []
        lp = self._row[self.LAUNCHPAD_HEADER]
        if lp:
            for bug in lp.split(","):
                if self._lp_reg.match(bug):
                    links.append(f"http://pad.lv/{bug}")
                else:
                    self.logger.warn(f"Unrecognized Bug: {bug}, title:{self.name}")
        return links

    def __repr__(self):
        return f"{self.product}:{self.name}"
