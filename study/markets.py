"""Save Kraken's spot market definitions (precision, minimums) for offline, reproducible backtests."""
from __future__ import annotations

import json
from pathlib import Path

from study.data import PRIMARY_PAIRS, SUPPORT_PAIRS

KEEP = ("id", "symbol", "base", "quote", "baseId", "quoteId", "settle", "settleId", "type",
        "spot", "margin", "swap", "future", "option", "active", "contract", "linear", "inverse",
        "taker", "maker", "contractSize", "expiry", "expiryDatetime", "strike", "optionType",
        "precision", "limits", "created", "altname", "wsId", "info")


def snapshot(markets: dict, pairs: list[str]) -> list[dict]:
    missing = [p for p in pairs if p not in markets]
    if missing:
        raise ValueError(f"Kraken does not list: {missing}")
    return [{k: markets[p].get(k) for k in KEEP} for p in pairs]


def main() -> int:  # pragma: no cover - network entry point
    import ccxt

    kraken = ccxt.kraken()
    markets = kraken.load_markets()
    out = Path("data/markets_kraken.json")
    out.write_text(json.dumps(snapshot(markets, PRIMARY_PAIRS + SUPPORT_PAIRS), indent=1, default=str) + "\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
