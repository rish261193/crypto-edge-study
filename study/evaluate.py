"""Turn backtest trade lists into the pre-registered verdicts and a results file."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from study import stats as S
from study.run import RunSpec

START_BALANCE = 500.0
VERDICT_SCENARIO = "base"
VERDICT_UNIVERSE = "primary"


def load_closes(datadir: Path, pairs: list[str]) -> pd.DataFrame:
    from freqtrade.data.history import load_pair_history

    cols = {}
    for pair in pairs:
        df = load_pair_history(pair=pair, timeframe="1d", datadir=datadir,
                               data_format="feather", fill_up_missing=False)
        if df.empty:
            continue
        cols[pair] = df.set_index("date")["close"]
    return pd.DataFrame(cols).sort_index()


def seed_for(text: str) -> int:
    return int(hashlib.sha256(text.encode()).hexdigest()[:8], 16)


def evaluation_days(closes: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DatetimeIndex:
    days = closes.index[(closes.index >= start) & (closes.index < end)]
    return pd.DatetimeIndex(days)


def evaluate_universe(results: dict[RunSpec, pd.DataFrame], closes: pd.DataFrame,
                      btc_close: pd.Series, start: pd.Timestamp, end: pd.Timestamp,
                      universe: str, scenario: str) -> dict:
    """closes: daily closes for this universe's pairs only."""
    days = evaluation_days(closes, start, end)
    asset_r = closes.reindex(days).pct_change().fillna(0.0)
    shifts = S.draw_shifts(len(days), np.random.default_rng(seed_for(f"shifts-{universe}")))
    rows, real_means, null_tables = {}, {}, {}
    for spec, trades in results.items():
        trades = trades[trades["open_date"] >= start]
        eq = S.daily_equity(trades, closes, START_BALANCE, days)
        r = S.returns(eq)
        exposure = S.daily_exposure(trades, closes, eq)
        model = S.exposure_model_returns(exposure, asset_r, spec.fee)
        nulls = S.null_means(exposure, asset_r, spec.fee, shifts)
        rng = np.random.default_rng(seed_for(spec.run_id))
        res = S.in_sample_verdict(r.to_numpy(), len(trades), float(model.mean()), nulls, rng)
        rm = S.r_multiples(trades)
        rows[spec.config_id] = {
            **res.as_dict(),
            "final_equity": float(eq.iloc[-1]),
            "mean_r_per_trade": float(rm.mean()) if len(rm) else None,
            "by_year": S.by_year(r),
            "by_regime": S.by_regime(r, btc_close),
        }
        real_means[spec.config_id] = float(model.mean())
        null_tables[spec.config_id] = nulls
    bh = closes.reindex(days).pct_change().mean(axis=1).dropna()
    return {
        "universe": universe, "scenario": scenario,
        "window": [days[0].isoformat(), (days[-1] + S.DAY).isoformat()],
        "configs": rows,
        "reality_check_pvalue": S.reality_check_pvalue(real_means, null_tables) if real_means else None,
        "benchmark_equal_weight_buy_and_hold": {"mean_daily": float(bh.mean()),
                                           "sharpe_annual": S.sharpe_annual(bh.to_numpy())},
    }


def save(result: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=1, default=float) + "\n")
