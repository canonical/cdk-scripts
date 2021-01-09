# from roadmap.logging import Logger


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
