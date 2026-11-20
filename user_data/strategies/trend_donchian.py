"""Family 1 (H1): time-series trend. Enter when the close breaks the prior N-bar high;
exit when it breaks the prior N/2-bar low. Stop: 3 x ATR(14). Expected sign: positive."""
import pandas as pd
from study_base import StudyBase


class TrendDonchian(StudyBase):
    STOP_ATR_MULT = 3.0
    DEFAULTS = {"n": 55}

    def populate_indicators(self, df: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        df = self.base_indicators(df)
        n = int(self.p["n"])
        df["upper"] = df["high"].rolling(n).max().shift(1)
        df["lower"] = df["low"].rolling(max(n // 2, 2)).min().shift(1)
        return df

    def populate_entry_trend(self, df: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        df.loc[df["close"] > df["upper"], "enter_long"] = 1
        return df

    def populate_exit_trend(self, df: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        df.loc[df["close"] < df["lower"], "exit_long"] = 1
        return df
