from datetime import datetime, timezone

import numpy as np
import pandas as pd
import pytest

from study import data as D


def hourly(start="2020-01-01", hours=24 * 10, price=100.0):
    idx = pd.date_range(start, periods=hours, freq="1h", tz="UTC")
    close = price + np.arange(hours, dtype=float)
    return pd.DataFrame({"date": idx, "open": close - 0.5, "high": close + 1, "low": close - 1,
                         "close": close, "volume": 1.0})


class FakeExchange:
    """Returns candles only from a listing date on; earlier windows are empty."""

    def __init__(self, listed, end):
        self.data = hourly(listed, int((pd.Timestamp(end, tz="UTC") - pd.Timestamp(listed, tz="UTC")) / pd.Timedelta(hours=1)))
        self.calls = 0

    def fetch_ohlcv(self, symbol, tf, since, limit):
        self.calls += 1
        ts = (self.data["date"] - pd.Timestamp(0, tz="UTC")) // pd.Timedelta(milliseconds=1)
        sel = self.data[(ts >= since) & (ts < since + limit * D.HOUR_MS)]
        return [[int((d - pd.Timestamp(0, tz="UTC")) // pd.Timedelta(milliseconds=1)), o, h, l, c, v] for d, o, h, l, c, v in sel.itertuples(index=False)]


def test_fetch_skips_empty_windows_before_listing():
    ex = FakeExchange("2020-03-01", "2020-03-11")
    df = D.fetch_hourly(ex, "BTC/USD", datetime(2020, 1, 1, tzinfo=timezone.utc),
                        datetime(2020, 3, 11, tzinfo=timezone.utc))
    assert df["date"].iloc[0] == pd.Timestamp("2020-03-01", tz="UTC")
    assert len(df) == 240 and df["date"].is_monotonic_increasing


def test_resample_4h_and_daily():
    h = hourly(hours=48)
    four = D.resample(h, "4h")
    assert len(four) == 12
    first = h.iloc[:4]
    assert four.iloc[0]["open"] == first["open"].iloc[0]
    assert four.iloc[0]["high"] == first["high"].max()
    assert four.iloc[0]["low"] == first["low"].min()
    assert four.iloc[0]["close"] == first["close"].iloc[-1]
    assert four.iloc[0]["volume"] == 4.0
    assert set(four["date"].dt.hour) == {0, 4, 8, 12, 16, 20}
    day = D.resample(h, "1D")
    assert len(day) == 2 and day["date"].iloc[1] == pd.Timestamp("2020-01-02", tz="UTC")


def test_split_never_leaks_holdout_into_insample():
    h = hourly(hours=24 * 800)
    s = D.Split.from_download_time(datetime(2022, 3, 5, 15, tzinfo=timezone.utc))
    ins, ho = D.split(h, s)
    assert ins["date"].max() < s.holdout_start <= ho["date"].min()
    assert ho["date"].max() < s.data_end
    assert s.data_end - s.holdout_start == pd.Timedelta(days=365)


def test_insample_freqtrade_files_end_before_holdout(tmp_path):
    from freqtrade.data.history import load_pair_history
    h = {"BTC/USD": hourly(hours=24 * 800), "ETH/USD": hourly(hours=24 * 800, price=10)}
    s = D.Split.from_download_time(datetime(2022, 3, 5, 15, tzinfo=timezone.utc))
    m = D.build(h, s, tmp_path, {"venue": "test"})
    for tf in ("4h", "1d"):
        ins = load_pair_history(pair="BTC/USD", timeframe=tf, datadir=tmp_path / "insample",
                                data_format="feather", fill_up_missing=False)
        assert ins["date"].max() < s.holdout_start
        full = load_pair_history(pair="BTC/USD", timeframe=tf, datadir=tmp_path / "sealed_full",
                                 data_format="feather", fill_up_missing=False)
        assert full["date"].max() >= s.holdout_start
    assert m["pairs"]["BTC/USD"]["insample_gaps"]["missing_hours"] == 0
    assert D.check_quality(m) == []


def test_gap_report_and_quality_failure():
    h = hourly(hours=1000).drop(index=range(100, 130)).reset_index(drop=True)
    g = D.gap_report(h)
    assert g["missing_hours"] == 30 and g["longest_gap_hours"] == 30
    m = {"pairs": {"BTC/USD": {"insample_gaps": g}, "ETH/USD": {"insample_gaps": D.gap_report(hourly(hours=50))}}}
    assert D.check_quality(m) == ["BTC/USD: 3.00% of hours missing"]


def test_validate_rejects_bad_candles():
    h = hourly(hours=10)
    bad = h.copy(); bad.loc[3, "high"] = bad.loc[3, "close"] - 5
    with pytest.raises(ValueError):
        D.validate(bad)
    with pytest.raises(ValueError):
        D.validate(pd.concat([h, h.iloc[[2]]]).reset_index(drop=True))


def test_canonical_hash_is_stable_and_sensitive():
    h = hourly(hours=10)
    assert D.canonical_sha256(h) == D.canonical_sha256(h.copy())
    changed = h.copy(); changed.loc[5, "close"] += 0.01
    assert D.canonical_sha256(changed) != D.canonical_sha256(h)


def test_incomplete_last_bar_is_dropped():
    h = hourly(hours=30)  # 1 full day + 6 hours
    day = D.resample(h, "1D")
    assert len(D.drop_incomplete_last_bar(day, "1D", h["date"].iloc[-1] + pd.Timedelta(hours=1))) == 1
