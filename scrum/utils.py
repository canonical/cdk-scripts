import confuse
from roadmap.github import RepoGroup
from roadmap.gsheets import ProductFeedback, Roadmap
from roadmap.trello import BacklogBoard, ScrumBoard, SizingBoard
from trello import TrelloClient


class CDKUtils:
    def __init__(self):
        self.config = confuse.Configuration("cdk-scripts")
        self.client = TrelloClient(
            self.config["Trello"]["api_key"].get(str),
            self.config["Trello"]["api_secret"].get(str),
        )

    def get_scrum_board(self, team):
        board = ScrumBoard(
            client=self.client,
            product_categories=self.config[team]["product_categories"].get(list),
            short_id=self.config[team]["scrum_id"].get(str),
        )
        return board

    def get_backlog_board(self, team):
        """Provide the config key as team"""
        board = BacklogBoard(
            client=self.client,
            short_id=self.config[team]["backlog_id"].get(str),
        )
        return board

    def get_sizing_board(self, team):
        """Provide the config key as team"""
        board = SizingBoard(
            client=self.client,
            short_id=self.config[team]["sizing_id"].get(str),
        )
        return board

    def get_product_roadmap(self, release, team=None):
        return Roadmap(
            key=self.config["Roadmap"]["key"].get(str),
            org=self.config["Roadmap"]["org"].get(str),
            team=team or self.config["Roadmap"]["team"].get(str),
            release=release,
        )

    def get_product_feedback(self, team):
        return ProductFeedback(
            key=self.config["Feedback"]["key"].get(str),
            product=self.config[team]["feedback_product"].get(str),
        )

    def get_repo_group(self, team):
        """Returns a RepoGroup for a given team based on team config"""
        gh_org = None
        gh_team = None
        gh_org = self.config[team]["github_org"].get(str)
        if self.config[team]["github_team"].exists():
            gh_team = self.config[team]["github_team"].get(list)
        rg = RepoGroup(
            self.config["Github"]["api_key"].get(str), org=gh_org, team=gh_team
        )
        return rg
