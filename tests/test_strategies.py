"""Strategy checks: no look-ahead in signals, and 1% risk sizing inside a real Freqtrade backtest."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "user_data" / "strategies"))

from mean_reversion import MeanReversion  # noqa: E402
from trend_donchian import TrendDonchian  # noqa: E402
from vol_breakout import VolBreakout  # noqa: E402

FAMILIES = [(TrendDonchian, {"n": 20}), (VolBreakout, {"m": 1.0}), (MeanReversion, {"threshold": 20})]


def candles(n=900, seed=4):
    rng = np.random.default_rng(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(0.0005, 0.03, n)))
    open_ = np.r_[100, close[:-1]]
    high = np.maximum(open_, close) * (1 + rng.uniform(0, 0.02, n))
    low = np.minimum(open_, close) * (1 - rng.uniform(0, 0.02, n))
    return pd.DataFrame({"date": pd.date_range("2018-01-01", periods=n, freq="1D", tz="UTC"),
                         "open": open_, "high": high, "low": low, "close": close, "volume": 1.0})


def make(cls, params):
    s = cls.__new__(cls)
    s.config = {"study_params": params}
    s.bot_start()
    return s


def signals(strategy, df):
    df = strategy.populate_indicators(df.copy(), {"pair": "BTC/USD"})
    df = strategy.populate_entry_trend(df, {"pair": "BTC/USD"})
    df = strategy.populate_exit_trend(df, {"pair": "BTC/USD"})
    cols = [c for c in ("enter_long", "exit_long", "atr") if c in df]
    return df[cols].fillna(0)


@pytest.mark.parametrize("cls,params", FAMILIES)
def test_signals_do_not_change_when_future_bars_are_removed(cls, params):
    df = candles()
    full = signals(make(cls, params), df)
    for cut in (300, 500, 700):
        part = signals(make(cls, params), df.iloc[:cut])
        pd.testing.assert_frame_equal(full.iloc[:cut], part, check_dtype=False)


@pytest.mark.parametrize("cls,params", FAMILIES)
def test_strategies_produce_entries(cls, params):
    assert signals(make(cls, params), candles())["enter_long"].sum() > 5


def test_unknown_parameter_is_rejected():
    s = TrendDonchian.__new__(TrendDonchian)
    s.config = {"study_params": {"nn": 3}}
    with pytest.raises(ValueError):
        s.bot_start()


@pytest.fixture(scope="module")
def synthetic_backtest(tmp_path_factory):
    from study import data as D
    from study import run as R
    tmp = tmp_path_factory.mktemp("bt")
    rng = np.random.default_rng(9)
    idx = pd.date_range("2019-01-01", "2023-01-01", freq="1h", tz="UTC", inclusive="left")
    hourly = {}
    for pair, p0 in (("BTC/USD", 5000.0), ("ETH/USD", 150.0)):
        c = p0 * np.exp(np.cumsum(rng.normal(0, 0.008, len(idx))))
        o = np.r_[p0, c[:-1]]
        hourly[pair] = pd.DataFrame({"date": idx, "open": o, "high": np.maximum(o, c) * 1.002,
                                     "low": np.minimum(o, c) * 0.998, "close": c, "volume": 1.0})
    s = D.Split.from_download_time(datetime(2023, 1, 1, 12, tzinfo=timezone.utc))
    D.build(hourly, s, tmp / "data", {"venue": "synthetic"})
    specs = [x for x in R.expand(R.load_grid(), ["base"], ["primary"])
             if x.timeframe == "1d" and x.value in (20, 1.0, 20)]
    out = {}
    for spec in specs:
        res = R.run_backtest(spec, tmp / "data" / "insample",
                             ROOT / "tests" / "fixtures" / "markets_kraken_fixture.json",
                             tmp / "runs", f"20190901-{s.holdout_start:%Y%m%d}")
        out[spec.family] = R.load_trades(res)
    return out


def test_every_family_runs_in_freqtrade(synthetic_backtest):
    assert set(synthetic_backtest) == {"TrendDonchian", "VolBreakout", "MeanReversion"}
    assert all(len(t) > 0 for t in synthetic_backtest.values())


def test_planned_risk_never_exceeds_one_percent_of_equity(synthetic_backtest):
    for family, trades in synthetic_backtest.items():
        trades = trades.sort_values("open_date").reset_index(drop=True)
        risk = trades["amount"] * (trades["open_rate"] - trades["stop_loss_abs"])
        assert (risk > 0).all(), family
        # equity before each entry is at most the starting balance plus all profit realised so far
        realised = [trades.loc[trades["close_date"] <= d, "profit_abs"].sum() for d in trades["open_date"]]
        ceiling = 0.01 * (500 + np.maximum(np.array(realised), 0) + 1e-6)
        # open positions can lift equity slightly above this ceiling; allow 10% headroom
        assert (risk <= ceiling * 1.10).all(), family
        assert risk.iloc[0] == pytest.approx(5.0, rel=0.02), family


def test_fees_are_charged_on_both_legs(synthetic_backtest):
    t = synthetic_backtest["TrendDonchian"]
    assert (t["fee_open"] == 0.0085).all() and (t["fee_close"] == 0.0085).all()


def test_trades_load_without_freqtrades_hidden_index(tmp_path, synthetic_backtest):
    """GitHub artifacts drop dotfiles; loading must not depend on .last_result.json."""
    import shutil
    from study import run as R
    src = next(p for p in Path(tmp_path).parent.glob("bt*/runs/*/results"))
    dst = tmp_path / "results"
    shutil.copytree(src, dst)
    for hidden in dst.glob(".*"):
        hidden.unlink()
    assert len(R.load_trades(dst)) > 0
