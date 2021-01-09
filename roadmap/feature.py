from roadmap.logging import Logger
import re


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
    def __init__(self, product, row):
        self.product = product
        self.logger = Logger()
        self._row = row
        self._lp_reg = re.compile(r'^\d{7}$')

    @property
    def name(self):
        return self._row.get("Title", "")

    @property
    def description(self):
        return self._row.get("Description", "")

    @property
    def story_points(self):
        return self._row.get("Duration", None)

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


class SizedFeature:
    pass


class FeatureStatus:
    def __init__(
        self,
        started=False,
        done=False,
        planned=True,
        at_risk=False,
        miss=False,
        dropped=False,
    ):
        # Set complete value
        if done:
            self.value = "C"
        else:
            self.value = ""

        # Set progress color
        if started:
            if not planned:
                self.color = "blue"
            else:
                self.color = "green"
        else:
            self.color = "white"

        # Set override colors
        if miss:
            self.color = "red"
        elif dropped:
            self.color = "black"
        elif at_risk:
            self.color = "orange"
