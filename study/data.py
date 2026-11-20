"""Download 1h candles, resample to 4h and 1d, seal the holdout, write a manifest.

Source: Coinbase Exchange public candles via CCXT (deep USD history, reachable
from GitHub-hosted runners). Kraken's API serves only 720 candles, and its full
trade history is too large to rebuild from trades; see PREREGISTRATION.md.
Fees in every backtest are Kraken's, because Kraken is where we would trade.
"""
from __future__ import annotations

import hashlib
import io
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

HOUR_MS = 3_600_000
COLUMNS = ["date", "open", "high", "low", "close", "volume"]
PRIMARY_PAIRS = ["BTC/USD", "ETH/USD"]
SUPPORT_PAIRS = ["LTC/USD", "LINK/USD", "XRP/USD", "ADA/USD", "SOL/USD", "DOT/USD"]
TIMEFRAMES = {"4h": "4h", "1d": "1D"}
HOLDOUT_DAYS = 365
MAX_MISSING_HOUR_SHARE = 0.01  # failure condition for BTC/ETH in-sample data


def fetch_hourly(exchange, symbol: str, start: datetime, end: datetime,
                 batch: int = 300) -> pd.DataFrame:
    """Page through 1h candles from start (inclusive) to end (exclusive).

    Empty windows (before listing, or outages) are skipped, not treated as the end."""
    since = int(start.timestamp() * 1000)
    stop = int(end.timestamp() * 1000)
    rows: list[list] = []
    while since < stop:
        chunk = exchange.fetch_ohlcv(symbol, "1h", since=since, limit=batch)
        chunk = [c for c in chunk if since <= c[0] < stop]
        if chunk:
            rows.extend(chunk)
            since = max(c[0] for c in chunk) + HOUR_MS
        else:
            since += batch * HOUR_MS
    df = pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume"])
    df = df.drop_duplicates("ts").sort_values("ts")
    df["date"] = pd.to_datetime(df.pop("ts"), unit="ms", utc=True)
    return df[COLUMNS].reset_index(drop=True)


def validate(df: pd.DataFrame) -> None:
    if df.empty:
        raise ValueError("No candles")
    if not df["date"].is_monotonic_increasing or df["date"].duplicated().any():
        raise ValueError("Candles must be strictly increasing")
    prices = df[["open", "high", "low", "close"]]
    if (prices <= 0).any().any() or df[["open", "high", "low", "close", "volume"]].isna().any().any():
        raise ValueError("Non-positive or missing values")
    if ((df["high"] < prices.max(axis=1) - 1e-9) | (df["low"] > prices.min(axis=1) + 1e-9)).any():
        raise ValueError("High/low inconsistent with open/close")


def gap_report(df: pd.DataFrame) -> dict:
    expected = pd.date_range(df["date"].iloc[0], df["date"].iloc[-1], freq="1h")
    missing = expected.difference(pd.DatetimeIndex(df["date"]))
    steps = df["date"].diff().dropna()
    return {
        "expected_hours": int(len(expected)),
        "missing_hours": int(len(missing)),
        "missing_share": round(len(missing) / max(len(expected), 1), 6),
        "longest_gap_hours": int(steps.max() / pd.Timedelta(hours=1)) - 1 if len(steps) else 0,
    }


def resample(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    """UTC-aligned OHLCV bars; bars with no trades at all are dropped (Freqtrade fills them flat)."""
    out = (df.set_index("date")
             .resample(rule, label="left", closed="left")
             .agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
             .dropna(subset=["open"])
             .reset_index())
    return out[COLUMNS]


def drop_incomplete_last_bar(bars: pd.DataFrame, rule: str, data_end: pd.Timestamp) -> pd.DataFrame:
    """Remove the final bar if its period extends past the data end."""
    if bars.empty:
        return bars
    last_end = bars["date"].iloc[-1] + pd.Timedelta(rule)
    return bars.iloc[:-1] if last_end > data_end else bars


def canonical_sha256(df: pd.DataFrame) -> str:
    buf = io.StringIO()
    out = df.copy()
    out["date"] = out["date"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    out.to_csv(buf, index=False, float_format="%.10g", lineterminator="\n")
    return hashlib.sha256(buf.getvalue().encode()).hexdigest()


@dataclass(frozen=True)
class Split:
    data_end: pd.Timestamp       # exclusive: start of the download day (UTC)
    holdout_start: pd.Timestamp  # in-sample is strictly before this

    @classmethod
    def from_download_time(cls, now: datetime) -> "Split":
        data_end = pd.Timestamp(now.astimezone(timezone.utc).date(), tz="UTC")
        return cls(data_end, data_end - pd.Timedelta(days=HOLDOUT_DAYS))


def split(df: pd.DataFrame, s: Split) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = df[df["date"] < s.data_end]
    return (df[df["date"] < s.holdout_start].reset_index(drop=True),
            df[df["date"] >= s.holdout_start].reset_index(drop=True))


def store_freqtrade(df: pd.DataFrame, datadir: Path, pair: str, timeframe: str) -> Path:
    from freqtrade.data.history.datahandlers import get_datahandler
    from freqtrade.enums import CandleType

    datadir.mkdir(parents=True, exist_ok=True)
    handler = get_datahandler(datadir, "feather")
    handler.ohlcv_store(pair, timeframe, df, CandleType.SPOT)
    return datadir


def build(pairs_hourly: dict[str, pd.DataFrame], s: Split, out: Path, source: dict) -> dict:
    """Write in-sample Freqtrade files, sealed holdout files, and return the manifest."""
    manifest = {"source": source, "data_end_exclusive": s.data_end.isoformat(),
                "holdout_start": s.holdout_start.isoformat(), "pairs": {}}
    for pair, hourly in pairs_hourly.items():
        validate(hourly)
        insample, holdout = split(hourly, s)
        entry = {"first_candle": insample["date"].iloc[0].isoformat() if len(insample) else None,
                 "insample_hours": int(len(insample)), "holdout_hours": int(len(holdout)),
                 "insample_gaps": gap_report(insample) if len(insample) else None,
                 "insample_sha256": canonical_sha256(insample),
                 "holdout_sha256": canonical_sha256(holdout)}
        for tf, rule in TIMEFRAMES.items():
            bars = drop_incomplete_last_bar(resample(insample, rule), rule, s.holdout_start)
            store_freqtrade(bars, out / "insample", pair, tf)
            hbars = drop_incomplete_last_bar(resample(hourly[hourly["date"] < s.data_end], rule), rule, s.data_end)
            store_freqtrade(hbars, out / "sealed_full", pair, tf)
        manifest["pairs"][pair] = entry
    return manifest


def check_quality(manifest: dict) -> list[str]:
    problems = []
    for pair in PRIMARY_PAIRS:
        entry = manifest["pairs"].get(pair)
        if entry is None or entry["insample_gaps"] is None:
            problems.append(f"{pair}: no in-sample data")
        elif entry["insample_gaps"]["missing_share"] > MAX_MISSING_HOUR_SHARE:
            problems.append(f"{pair}: {entry['insample_gaps']['missing_share']:.2%} of hours missing")
    return problems


def main() -> int:  # pragma: no cover - network entry point, run in GitHub Actions
    import argparse
    import ccxt

    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="user_data/data")
    parser.add_argument("--manifest", default="data/manifest.json")
    parser.add_argument("--start", default="2015-01-01")
    args = parser.parse_args()
    now = datetime.now(timezone.utc)
    s = Split.from_download_time(now)
    exchange = ccxt.coinbaseexchange({"enableRateLimit": True})
    start = datetime.fromisoformat(args.start).replace(tzinfo=timezone.utc)
    hourly = {p: fetch_hourly(exchange, p, start, s.data_end.to_pydatetime())
              for p in PRIMARY_PAIRS + SUPPORT_PAIRS}
    source = {"venue": "Coinbase Exchange public candles", "ccxt_id": "coinbaseexchange",
              "ccxt_version": ccxt.__version__, "retrieved_utc": now.isoformat(), "timeframe": "1h"}
    manifest = build(hourly, s, Path(args.out), source)
    manifest["quality_problems"] = check_quality(manifest)
    Path(args.manifest).parent.mkdir(parents=True, exist_ok=True)
    Path(args.manifest).write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest["quality_problems"]))
    return 1 if manifest["quality_problems"] else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
