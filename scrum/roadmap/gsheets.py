import gspread
import gspread_formatting
import pandas as pd
from roadmap.feature import FeedbackFeature, RoadmapFeature
from roadmap.logging import Logger


class Roadmap:
    def __init__(self, key, org, team, release):
        self.release = release
        self.team = team
        self.logger = Logger()
        self._client = gspread.oauth()
        self._sh = self._client.open_by_key(key)
        self._ws = self._sh.worksheet(org)
        self._df = None

    @property
    def df(self):
        if self._df is not None:
            return self._df
        df = pd.DataFrame(
            self._ws.get_all_values(),
            dtype="string",
        )
        df.columns = df.loc[0, :].tolist()
        df.columns.values[0] = "Labels"
        df.set_index("Labels", inplace=True, drop=False)
        self._df = df
        return df

    @property
    def next_release(self):
        # Return the next non blank label
        slice = self.df["Labels"][self.release :].iloc[1:]
        return slice.loc[slice.ne("")].iloc[0]

    def get_features(self):
        values = self.df.loc[self.release : self.next_release, self.team].iloc[:-1]
        category = None
        features = []
        for entry in values:
            if not category:
                if entry:
                    category = entry
            elif not entry:
                category = None
            else:
                features.append(
                    RoadmapFeature(
                        name=entry,
                        category=category,
                        release=self.release,
                        team=self.team,
                    )
                )
        return features

    def status_to_color(self, status):
        product_colors = {
            "green": "#6aa84f",
            "blue": "#3d85c6",
            "orange": "#e69138",
            "red": "#cc0000",
            "black": "#000000",
            "white": "#ffffff",
        }
        # These colors show regardless of current progress
        if status.color in ["red", "orange", "black"]:
            return gspread_formatting.Color.fromHex(product_colors[status.color])
        # Return the color if feature has started
        elif status.state != status.NOT_STARTED:
            return gspread_formatting.Color.fromHex(product_colors[status.color])
        else:
            return gspread_formatting.Color.fromHex(product_colors["white"])

    def status_to_value(self, status):
        if status.state == status.DONE:
            return "C"

    def update_features(self, trello_features):
        name_list = (
            self.df.loc[self.release : self.next_release, self.team].iloc[:-1].tolist()
        )
        status_col = self.df.columns.get_loc(self.team)  # works b/c pd is zero based
        self.logger.debug(f"DEBUG: {self.df.columns.has_duplicates}")
        value_updates = []
        format_updates = []
        for feature in trello_features:
            self.logger.debug(f"Starting on {feature}")
            if feature.release != self.release:
                raise ValueError(
                    "Only features matching the current release can be updated."
                    "Current Release: {self.release}"
                    "Feature Release: {feature.release}"
                    "Feature Name:    {feature.name}"
                )
            feature_row = (
                name_list.index(feature.name)
                + self.df.index.get_loc(self.release)
                + 1  # Index is zero based
            )
            a1 = gspread.utils.rowcol_to_a1(feature_row, status_col)
            fmt = gspread_formatting.cellFormat(
                backgroundColor=self.status_to_color(feature.status),
                horizontalAlignment="CENTER",
                textFormat=gspread_formatting.textFormat(
                    bold=True,
                    foregroundColor=gspread_formatting.Color.fromHex("#ffffff"),
                ),
            )
            value_updates.append(
                {
                    "range": a1,
                    "values": [
                        [
                            self.status_to_value(feature.status),
                        ]
                    ],
                }
            )
            format_updates.append((a1, fmt))
            self.logger.debug(f"Row: {feature_row}")
            self.logger.debug(f"Col: {status_col}")
            self.logger.debug(f"A1: {a1}")
        self._ws.batch_update(value_updates)
        gspread_formatting.format_cell_ranges(self._ws, format_updates)
        self._df = None


class ProductFeedback:
    RESOLVED_COLUMN = "Resolved"
    SIZE_COLUMN = "Duration"

    def __init__(self, key, product):
        self.logger = Logger()
        self._client = gspread.oauth()
        self._sh = self._client.open_by_key(key)
        self._product = product
        self._ws = self._sh.worksheet(product)
        self._df = None

    @property
    def df(self):
        if self._df is not None:
            return self._df
        df = pd.DataFrame(
            self._ws.get_all_records(),
            dtype="string",
        )
        df.set_index("Title", inplace=True, drop=False)
        self._df = df
        return df

    @property
    def all_features(self):
        """Return all feedback features"""
        features = []
        for feature in self.df.to_dict("records"):
            features.append(FeedbackFeature(self._product, feature))
        return features

    def get_features(self, active=True):
        """Return features"""
        all = self.all_features
        if active:
            result = list(filter(lambda x: not x.resolved, all))
        else:
            result = all
        self.logger.debug(f"Active: {active}")
        return result

    def add_titles(self, words=8):
        # Build series of truncated descriptions
        truncated = (
            self.df["Description"].str.split(r"\s", expand=True).iloc[:, 0:words]
        )
        titles = truncated.fillna("").apply(" ".join, axis=1)
        # Find range for writting
        title_column = self.df.columns.get_loc("Title") + 1  # zero based
        last_row = len(self.df.index) + 1  # zero based
        a1_start = gspread.utils.rowcol_to_a1(2, title_column)
        a1_end = gspread.utils.rowcol_to_a1(last_row, title_column)
        a1_range = f"{a1_start}:{a1_end}"
        # Update sheet
        self._ws.update(a1_range, [titles.tolist()], major_dimension="COLUMNS")

    def update_features(self, sized_features):
        self.logger.info("Updating feedback sizes")
        if type(self.df["Title"]) is None:
            raise ValueError("Title header not found in product feedback")
        title_list = self._df["Title"].tolist()
        size_col = self.df.columns.get_loc(self.SIZE_COLUMN) + 1  # zero based
        status_col = self.df.columns.get_loc(self.RESOLVED_COLUMN) + 1  # zero based
        value_updates = []
        for sized_feature in sized_features:
            # +1 for zero based and 1 to account for header
            try:
                row = title_list.index(sized_feature.name) + 2
            except ValueError:
                self.logger.debug(
                    f"Skipp feature, not on feedback: '{sized_feature.name}'"
                )
                # No title
                continue
            a1_size = gspread.utils.rowcol_to_a1(row, size_col)
            # Update size
            value_updates.append(
                {
                    "range": a1_size,
                    "values": [
                        [
                            sized_feature.story_points,
                        ],
                    ],
                }
            )
            # Update status
            a1_status = gspread.utils.rowcol_to_a1(row, status_col)
            status = self._get_feature_status(sized_feature)
            value_updates.append(
                {
                    "range": a1_status,
                    "values": [
                        [
                            status,
                        ],
                    ],
                }
            )
        self._ws.batch_update(value_updates)

    def _get_feature_status(self, feature):
        """Return a status compatible with the gsheet based on a feature"""
        status = False
        try:
            if feature.status.value == feature.DONE:
                status = True
        except AttributeError:
            # Not a Scrum Status
            pass
        if feature.closed:
            status = True
        return status
