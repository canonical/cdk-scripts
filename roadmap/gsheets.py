import gspread
import gspread_formatting
import pandas as pd
from roadmap.feature import RoadmapFeature
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
        if status.color == "green":
            return gspread_formatting.Color.fromHex("#6aa84f")
        elif status.color == "blue":
            return gspread_formatting.Color.fromHex("#3d85c6")
        elif status.color == "orange":
            return gspread_formatting.Color.fromHex("#e69138")
        elif status.color == "red":
            return gspread_formatting.Color.fromHex("#cc0000")
        elif status.color == "black":
            return gspread_formatting.Color.fromHex("#000000")
        else:
            return gspread_formatting.Color.fromHex("#ffffff")

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
                            feature.status.value,
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
