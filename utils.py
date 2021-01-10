import confuse
from roadmap.gsheets import Roadmap
from roadmap.trello import ScrumBoard
from trello import TrelloClient


class CDKUtils:
    def __init__(self):
        self.config = confuse.Configuration("cdk-scripts")
        self.client = TrelloClient(
            self.config["Trello"]["api_key"].get(str),
            self.config["Trello"]["api_secret"].get(str),
        )

    def get_scrum_boards(self):
        scrum_boards = []
        cdk = ScrumBoard(
            client=self.client,
            product_categories=self.config["CDK"]["product_categories"].get(list),
            id=self.config["CDK"]["board_id"].get(str),
        )
        scrum_boards.append(cdk)
        # mk8s = ScrumBoard(
        #     client=self.client,
        #     product_categories=self.config["MicroK8s"]["product_categories"],
        #     id=self.config["MicroK8s"]["board_id"],
        # )
        # scrum_boards.append(mk8s)
        # kf = ScrumBoard(
        #     client=client,
        #     product_categories=self.config["Kubeflow"]["product_categories"],
        #     id=self.config["Kubeflow"]["board_id"],
        # )
        # scrum_boards.append(kf)
        return scrum_boards

    def get_product_roadmap(self, release):
        return Roadmap(
            key=self.config["Roadmap"]["key"].get(str),
            org=self.config["Roadmap"]["org"].get(str),
            team=self.config["Roadmap"]["team"].get(str),
            release=release
        )
