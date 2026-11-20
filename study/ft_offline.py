"""Run a Freqtrade command against a saved market snapshot instead of the live exchange.

Why: backtests must be reproducible after the exchange changes its market list,
and must run without network access. Usage:

    python -m study.ft_offline <markets.json> backtesting --config ... [freqtrade args]

The snapshot is a JSON list of ccxt market dicts, produced by study.markets.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def install_market_snapshot(markets: list[dict]) -> None:
    from freqtrade.exchange import exchange as ft_exchange
    from freqtrade.util import dt_ts

    def reload_markets(self, force: bool = False, *, load_leverage_tiers: bool = True) -> None:
        if self._last_markets_refresh > 0 and not force:
            return
        for api in (self._api, self._api_async):
            api.set_markets(markets)
        self._markets = self._api.markets
        self._last_markets_refresh = dt_ts()

    ft_exchange.Exchange.reload_markets = reload_markets


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    markets = json.loads(Path(argv[0]).read_text())
    if not isinstance(markets, list) or not markets:
        raise SystemExit("Market snapshot must be a non-empty JSON list")
    install_market_snapshot(markets)
    from freqtrade.main import main as ft_main

    try:
        ft_main(argv[1:])
    except SystemExit as exc:  # freqtrade exits via SystemExit
        return int(exc.code or 0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
