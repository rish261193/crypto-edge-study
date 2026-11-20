"""Shared rules for every pre-registered strategy family (see PREREGISTRATION.md).

Long-only spot. Each trade risks 1% of current equity: the position is sized so
that hitting the ATR stop loses 1% (before fees and slippage). The stop is fixed
at entry: open price minus STOP_ATR_MULT x ATR(14) of the signal candle.
"""
from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd
from freqtrade.exchange import timeframe_to_minutes, timeframe_to_prev_date
from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy, stoploss_from_absolute

RISK_FRACTION = 0.01
ATR_PERIOD = 14


def wilder(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()


def atr(df: pd.DataFrame, period: int = ATR_PERIOD) -> pd.Series:
    prev_close = df["close"].shift(1)
    true_range = pd.concat(
        [df["high"] - df["low"], (df["high"] - prev_close).abs(), (df["low"] - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    return wilder(true_range, period)


def rsi(close: pd.Series, period: int) -> pd.Series:
    delta = close.diff()
    gain = wilder(delta.clip(lower=0), period)
    loss = wilder(-delta.clip(upper=0), period)
    rs = gain / loss.replace(0, np.nan)
    out = 100 - 100 / (1 + rs)
    return out.where(loss != 0, 100.0)


class StudyBase(IStrategy):
    INTERFACE_VERSION = 3
    can_short = False
    timeframe = "1d"  # every run sets the timeframe in its config
    startup_candle_count = 250
    process_only_new_candles = True
    minimal_roi = {"0": 100.0}  # profit-taking disabled; exits come from the rules
    stoploss = -0.99  # placeholder; the real stop is custom_stoploss
    use_custom_stoploss = True
    trailing_stop = False
    use_exit_signal = True
    exit_profit_only = False
    order_types = {
        "entry": "market",
        "exit": "market",
        "stoploss": "market",
        "stoploss_on_exchange": False,
    }

    STOP_ATR_MULT: float = 3.0
    MAX_HOLD_BARS: int | None = None
    DEFAULTS: dict = {}

    def bot_start(self, **kwargs) -> None:
        unknown = set(self.config.get("study_params", {})) - set(self.DEFAULTS)
        if unknown:
            raise ValueError(f"Unknown study parameters: {sorted(unknown)}")
        self.p = {**self.DEFAULTS, **self.config.get("study_params", {})}

    # --- shared indicators -------------------------------------------------
    def base_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df["atr"] = atr(df)
        return df

    # --- sizing: 1% of equity at risk to the stop ------------------------
    def custom_stake_amount(self, pair: str, current_time: datetime, current_rate: float,
                            proposed_stake: float, min_stake: float | None, max_stake: float,
                            leverage: float, entry_tag: str | None, side: str,
                            **kwargs) -> float:
        df, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if df.empty:
            return 0.0
        signal_atr = float(df["atr"].iloc[-1])
        stop_distance = self.STOP_ATR_MULT * signal_atr
        if not np.isfinite(stop_distance) or stop_distance <= 0 or stop_distance >= current_rate:
            return 0.0
        equity = self.wallets.get_total_stake_amount()
        quantity = RISK_FRACTION * equity / stop_distance
        stake = quantity * current_rate
        if stake > max_stake:
            stake = max_stake  # no leverage: risk is then below 1%
        if min_stake is not None and stake < min_stake:
            return 0.0  # below the exchange minimum: skip rather than over-risk
        return stake

    # --- fixed ATR stop set at entry --------------------------------------
    def stop_price(self, pair: str, trade: Trade) -> float | None:
        df, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        entry_candle = timeframe_to_prev_date(self.timeframe, trade.open_date_utc)
        signal_date = entry_candle - pd.Timedelta(minutes=timeframe_to_minutes(self.timeframe))
        row = df.loc[df["date"] == signal_date]
        if row.empty:
            return None
        return trade.open_rate - self.STOP_ATR_MULT * float(row["atr"].iloc[0])

    def custom_stoploss(self, pair: str, trade: Trade, current_time: datetime,
                        current_rate: float, current_profit: float, after_fill: bool,
                        **kwargs) -> float | None:
        stop = self.stop_price(pair, trade)
        if stop is None or stop <= 0:
            return None  # keep the previous stop
        return stoploss_from_absolute(stop, current_rate, is_short=False)

    # --- optional time exit -------------------------------------------------
    def custom_exit(self, pair: str, trade: Trade, current_time: datetime, current_rate: float,
                    current_profit: float, **kwargs) -> str | None:
        if self.MAX_HOLD_BARS is None:
            return None
        held = (current_time - trade.open_date_utc).total_seconds() / 60
        if held >= self.MAX_HOLD_BARS * timeframe_to_minutes(self.timeframe):
            return "time_exit"
        return None
