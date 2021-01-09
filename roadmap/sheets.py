import pickle
import pprint
from functools import lru_cache
from pathlib import Path

from google.auth.transport.requests import Request

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient import discovery
from roadmap.feature import RoadmapFeature

# from roadmap.config import Config
from roadmap.logging import Logger

cache = lru_cache(maxsize=None)


class Spreadsheet:
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    # CONFIG_SECTION = ""

    def __init__(self, id, credential_path="."):
        self.id = id
        self.credential_path = Path(credential_path)
        self.logger = Logger()
        # self.config = Config().get_config(self.CONFIG_SECTION)
        self._services = None

    @property
    @cache
    def service(self):
        creds = self._get_credentials()
        service = discovery.build("sheets", "v4", credentials=creds)

        return service

    def _get_credentials(self):
        # config_dir = Path(Config().get_config().config_dir())
        token_file = self.credential_path / "Token" / f"{self.id}.pickle"
        self.logger.debug(f"Using token file: {token_file}")

        creds = None
        if token_file.exists():
            with token_file.open("rb") as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credential_path / "credentials.json"), self.SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save the credentials for the next run
            token_file.parents[0].mkdir(parents=True, exist_ok=True)
            token_file.touch(exist_ok=True)
            with token_file.open("wb") as token:
                pickle.dump(creds, token)

        return creds

    def get(self, ranges=[], includeGridData=False):
        request = self.service.spreadsheets().get(
            spreadsheetId=self.id, ranges=ranges, includeGridData=includeGridData
        )
        response = request.execute()
        pp = pprint.PrettyPrinter(indent=2)
        self.logger.debug(pp.pprint(response))


class Roadmap(Spreadsheet):
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    # CONFIG_SECTION = "Roadmap"

    def __init__(self, org, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.org = org
        # self.id = self.config["id"].get(str)

    @property
    @cache
    def values(self):
        # range = self.config["group"].get(str)
        range = self.org
        self.logger.debug(f"Getting values for: {range}")
        request = (
            self.service.spreadsheets().values().get(spreadsheetId=self.id, range=range)
        )
        result = request.execute()
        values = result.get("values", [])
        return values

    @cache
    def _get_team_index(self, team):
        # team_index = self.values[0].index(self.config["team"].get(str))
        team_index = self.values[0].index(team)
        return team_index

    @cache
    def _get_release_index(self, release):
        release_index = None
        for i, row in enumerate(self.values):
            try:
                if row[0].strip() == release:
                    release_index = i
                    break
            except IndexError:
                pass
        return release_index

    def get_features(self, team, release):
        team_index = self._get_team_index(team)
        release_index = self._get_release_index(release)
        self.logger.debug(f"TeamIDX: {team_index}")
        self.logger.debug(f"ReleaseIDX: {release_index}")
        feature_matrix = map(
            lambda x: x[team_index - 1 : team_index + 1],
            self.values[release_index + 1 :],
        )
        features = []
        category_active = False
        for i, row in enumerate(feature_matrix):
            self.logger.debug(f"Processing row: {row}")
            if not len(row):
                name = None
                status = None
            else:
                name = row[1]
                status = row[0]

            if not category_active:
                if name:
                    category = name
                    # items[category] = []
                    category_active = True
                    self.logger.debug(f"Starting category: {category}")
                else:
                    # No category or name we're done
                    break
            elif not name:
                # End the category when we get a blank
                category_active = False
            else:
                # +1 because we start itterating 1 below the release index
                index = release_index + 1 + i
                feature = RoadmapFeature(
                    roadmap=self,
                    category=category,
                    team=team,
                    name=name,
                    release=release,
                    index=index,
                    status=status,
                )
                features.append(feature)
        return features
