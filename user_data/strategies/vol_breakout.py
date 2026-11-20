"""Family 2 (H2): volatility-expansion breakout. Enter when a bar closes more than
m x ATR(14) above the previous close; exit after 10 bars. Stop: 2 x ATR(14).
Expected sign: positive."""
import pandas as pd
from study_base import StudyBase


class VolBreakout(StudyBase):
    STOP_ATR_MULT = 2.0
    MAX_HOLD_BARS = 10
    DEFAULTS = {"m": 1.5}

    def populate_indicators(self, df: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        return self.base_indicators(df)

    def populate_entry_trend(self, df: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        jump = df["close"] - df["close"].shift(1)
        df.loc[jump > float(self.p["m"]) * df["atr"].shift(1), "enter_long"] = 1
        return df

    def populate_exit_trend(self, df: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        return df  # time exit and stop only
