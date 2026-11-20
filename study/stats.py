"""Daily equity, bootstrap confidence bounds, timing-shift nulls and verdicts.

All rules here are fixed by PREREGISTRATION.md. Constants below must match it.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd

DAY = pd.Timedelta(days=1)
BLOCK_DAYS = 20
N_BOOTSTRAP = 10_000
N_NULLS = 1_000
MIN_SHIFT_DAYS = 30
LOWER_QUANTILE = 0.05          # one-sided 95% lower bound
NULL_PERCENTILE_GATE = 0.95    # beat at least 95% of nulls
MIN_TRADES = 50                # sanity floor only
HOLDOUT_DAYS = 365
FAIL_NULL_PERCENTILE = 0.50    # no better than a typical random strategy


# --- equity -------------------------------------------------------------------

def daily_equity(trades: pd.DataFrame, closes: pd.DataFrame, start_balance: float,
                 days: pd.DatetimeIndex) -> pd.Series:
    """Mark-to-market equity at the end of each UTC day.

    closes: daily close prices, index = day start (UTC), one column per pair.
    Closed trades contribute their realised profit_abs (net of fees) from the day
    they close; open trades contribute amount x (close - open_rate) less the entry fee.
    """
    equity = pd.Series(float(start_balance), index=days)
    day_end = days + DAY
    for t in trades.itertuples(index=False):
        closed = day_end > t.close_date
        is_open = (day_end > t.open_date) & ~closed
        equity[closed] += t.profit_abs
        if is_open.any():
            px = closes[t.pair].reindex(days[is_open]).ffill()
            entry_fee = t.amount * t.open_rate * t.fee_open
            equity[is_open] += (t.amount * (px.to_numpy() - t.open_rate) - entry_fee)
    return equity


def daily_exposure(trades: pd.DataFrame, closes: pd.DataFrame, equity: pd.Series) -> pd.DataFrame:
    """Fraction of equity held in each pair at the end of each day."""
    days = equity.index
    day_end = days + DAY
    value = pd.DataFrame(0.0, index=days, columns=closes.columns)
    for t in trades.itertuples(index=False):
        held = (day_end > t.open_date) & (day_end <= t.close_date)
        if held.any():
            px = closes[t.pair].reindex(days[held]).ffill().to_numpy()
            value.loc[held, t.pair] += t.amount * px
    return value.div(equity, axis=0)


def returns(equity: pd.Series) -> pd.Series:
    return equity.pct_change().dropna()


# --- bootstrap ----------------------------------------------------------------

def circular_block_means(x: np.ndarray, length: int, n: int, block: int,
                         rng: np.random.Generator) -> np.ndarray:
    """Means of n circular-block-bootstrap resamples of the given length."""
    x = np.asarray(x, dtype=float)
    t = len(x)
    if t < block:
        raise ValueError("Series shorter than one block")
    n_blocks = -(-length // block)
    starts = rng.integers(0, t, size=(n, n_blocks))
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]) % t
    idx = idx.reshape(n, -1)[:, :length]
    return x[idx].mean(axis=1)


def lower_bound(x: np.ndarray, rng: np.random.Generator, n: int = N_BOOTSTRAP) -> float:
    return float(np.quantile(circular_block_means(x, len(x), n, BLOCK_DAYS, rng), LOWER_QUANTILE))


def holdout_floor(x: np.ndarray, rng: np.random.Generator, n: int = N_BOOTSTRAP) -> float:
    """5th percentile of the mean over a 365-day window, resampled from in-sample days."""
    return float(np.quantile(circular_block_means(x, HOLDOUT_DAYS, n, BLOCK_DAYS, rng), LOWER_QUANTILE))


# --- timing-shift null ----------------------------------------------------------

def exposure_model_returns(exposure: pd.DataFrame, asset_returns: pd.DataFrame,
                           fee: float) -> np.ndarray:
    """Daily net return of holding yesterday's exposure, paying `fee` on traded fraction."""
    e = exposure.to_numpy()
    r = asset_returns.to_numpy()
    prev = np.vstack([np.zeros((1, e.shape[1])), e[:-1]])
    turnover = np.abs(e - prev).sum(axis=1)
    return (prev * r).sum(axis=1) - fee * turnover


def draw_shifts(n_days: int, rng: np.random.Generator, n: int = N_NULLS) -> np.ndarray:
    if n_days <= 2 * MIN_SHIFT_DAYS:
        raise ValueError("Too few days for timing-shift nulls")
    return rng.integers(MIN_SHIFT_DAYS, n_days - MIN_SHIFT_DAYS, size=n)


def null_means(exposure: pd.DataFrame, asset_returns: pd.DataFrame, fee: float,
               shifts: np.ndarray) -> np.ndarray:
    """Mean daily net return of the same exposure pattern, shifted in time.

    Same exposure, turnover and holding periods; only the timing changes, so a
    strategy with no timing skill sits in the middle of this distribution."""
    e = exposure.to_numpy()
    out = np.empty(len(shifts))
    for i, k in enumerate(shifts):
        shifted = pd.DataFrame(np.roll(e, int(k), axis=0), index=exposure.index,
                               columns=exposure.columns)
        out[i] = exposure_model_returns(shifted, asset_returns, fee).mean()
    return out


# --- verdicts -----------------------------------------------------------------

@dataclass
class InSampleResult:
    days: int
    trades: int
    mean_daily: float
    lower_bound_daily: float
    sharpe_annual: float
    null_percentile: float
    gate_ci: bool
    gate_nulls: bool
    gate_trades: bool
    verdict: str  # PASS_INSAMPLE | INCONCLUSIVE | FAIL

    def as_dict(self) -> dict:
        return asdict(self)


def sharpe_annual(r: np.ndarray) -> float:
    sd = float(np.std(r, ddof=1))
    return float(np.mean(r) / sd * np.sqrt(365)) if sd > 0 else 0.0


def in_sample_verdict(r: np.ndarray, n_trades: int, model_mean: float,
                      nulls: np.ndarray, rng: np.random.Generator) -> InSampleResult:
    mean = float(np.mean(r))
    lb = lower_bound(r, rng)
    pct = float(np.mean(nulls < model_mean))
    g1, g2, g3 = lb > 0, pct >= NULL_PERCENTILE_GATE, n_trades >= MIN_TRADES
    if g1 and g2 and g3:
        verdict = "PASS_INSAMPLE"
    elif mean <= 0 or pct < FAIL_NULL_PERCENTILE:
        verdict = "FAIL"
    else:
        verdict = "INCONCLUSIVE"
    return InSampleResult(len(r), n_trades, mean, lb, sharpe_annual(r), pct, g1, g2, g3, verdict)


def final_verdict(in_sample: str, holdout_mean: float | None, floor: float | None) -> str:
    if in_sample != "PASS_INSAMPLE":
        return in_sample
    if holdout_mean is None or floor is None:
        raise ValueError("Holdout needed for configurations that passed in-sample")
    return "PASS" if holdout_mean >= floor else "FAIL"


def reality_check_pvalue(real_means: dict[str, float], null_tables: dict[str, np.ndarray]) -> float:
    """Family-wise view (reported, not a gate): how often the best of the shifted
    configurations beats the best real configuration, using the same shifts for all."""
    best_real = max(real_means.values())
    stacked = np.vstack(list(null_tables.values()))
    return float(np.mean(stacked.max(axis=0) >= best_real))


# --- diagnostics ---------------------------------------------------------------

def r_multiples(trades: pd.DataFrame) -> pd.Series:
    """Net profit per trade in units of planned risk at entry (amount x stop distance)."""
    risk = trades["amount"] * (trades["open_rate"] - trades["stop_loss_abs"])
    return trades["profit_abs"] / risk.where(risk > 0)


def by_year(r: pd.Series) -> dict[str, float]:
    return {str(y): float(v) for y, v in r.groupby(r.index.year).mean().items()}


def by_regime(r: pd.Series, btc_close: pd.Series) -> dict[str, float]:
    """Bull = BTC daily close above its 200-day average on the previous day."""
    sma = btc_close.rolling(200).mean()
    bull = (btc_close > sma).shift(1).reindex(r.index)
    out = {}
    for name, mask in (("bull", bull == True), ("bear", bull == False)):  # noqa: E712
        out[name] = float(r[mask].mean()) if mask.any() else None
    return out
