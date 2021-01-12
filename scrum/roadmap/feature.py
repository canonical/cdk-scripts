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


class TrelloFeature(BaseFeature):
    def __init__(self, board, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.board = board

    def __repr__(self):
        return f"{self.release}:{self.name}:{self.status.value}"


class FeedbackFeature:
    RESOLVED_HEADER = "Resolved"
    DESCRIPTION_HEADER = "Description"
    TITLE_HEADER = "Title"
    STORY_POINTS_HEADER = "Duration"

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
        return title

    @property
    def description(self):
        return self._row.get(self.DESCRIPTION_HEADER, "")

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
        lp = self._row["LP"]
        if lp:
            for bug in lp.split(","):
                if self._lp_reg.match(bug):
                    links.append(f"http://pad.lv/{bug}")
                else:
                    self.logger.warn(f"Unrecognized Bug: {bug}, title:{self.name}")
        return links

    def __repr__(self):
        return f"{self.product}:{self.name}"
