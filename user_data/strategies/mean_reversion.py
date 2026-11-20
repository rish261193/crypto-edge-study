"""Family 3 (H3, control): short-horizon mean reversion. Enter when RSI(2) is below a
threshold while the close is above its 200-bar average; exit when the close rises
above its 5-bar average, or after 5 bars. Stop: 3 x ATR(14). Expected: any gross
edge is consumed by fees (many short trades)."""
import pandas as pd
from study_base import StudyBase, rsi


class MeanReversion(StudyBase):
    STOP_ATR_MULT = 3.0
    MAX_HOLD_BARS = 5
    DEFAULTS = {"threshold": 10}

    def populate_indicators(self, df: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        df = self.base_indicators(df)
        df["rsi2"] = rsi(df["close"], 2)
        df["sma200"] = df["close"].rolling(200).mean()
        df["sma5"] = df["close"].rolling(5).mean()
        return df

    def populate_entry_trend(self, df: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        cond = (df["rsi2"] < float(self.p["threshold"])) & (df["close"] > df["sma200"])
        df.loc[cond, "enter_long"] = 1
        return df

    def populate_exit_trend(self, df: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        df.loc[df["close"] > df["sma5"], "exit_long"] = 1
        return df
