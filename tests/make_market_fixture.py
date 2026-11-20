"""Build tests/fixtures/markets_kraken_fixture.json offline, by feeding ccxt's own Kraken
parser hand-written AssetPairs entries. For tests only; real runs use data/markets_kraken.json."""
import json
from pathlib import Path

import ccxt

PAIRS = {  # id: (altname, wsname, base, quote, pair_decimals, ordermin)
    "XXBTZUSD": ("XBTUSD", "XBT/USD", "XXBT", "ZUSD", 1, "0.0001"),
    "XETHZUSD": ("ETHUSD", "ETH/USD", "XETH", "ZUSD", 2, "0.01"),
    "XLTCZUSD": ("LTCUSD", "LTC/USD", "XLTC", "ZUSD", 2, "0.05"),
    "LINKUSD": ("LINKUSD", "LINK/USD", "LINK", "ZUSD", 5, "0.2"),
    "XXRPZUSD": ("XRPUSD", "XRP/USD", "XXRP", "ZUSD", 5, "2"),
    "ADAUSD": ("ADAUSD", "ADA/USD", "ADA", "ZUSD", 6, "5"),
    "SOLUSD": ("SOLUSD", "SOL/USD", "SOL", "ZUSD", 2, "0.02"),
    "DOTUSD": ("DOTUSD", "DOT/USD", "DOT", "ZUSD", 4, "0.6"),
}


def main():
    k = ccxt.kraken()
    raw = {}
    for pid, (alt, ws, base, quote, pd_, omin) in PAIRS.items():
        raw[pid] = {"altname": alt, "wsname": ws, "aclass_base": "currency", "base": base,
                    "aclass_quote": "currency", "quote": quote, "lot": "unit", "cost_decimals": 5,
                    "pair_decimals": pd_, "lot_decimals": 8, "lot_multiplier": 1,
                    "leverage_buy": [], "leverage_sell": [], "fees": [[0, 0.8]],
                    "fees_maker": [[0, 0.4]], "fee_volume_currency": "ZUSD", "margin_call": 80,
                    "margin_stop": 40, "ordermin": omin, "costmin": "0.5",
                    "tick_size": str(10 ** -pd_), "status": "online"}
    k.public_get_assetpairs = lambda params={}: {"error": [], "result": raw}
    k.publicGetAssetPairs = k.public_get_assetpairs
    k.fetch_currencies = lambda params={}: {}
    out = Path(__file__).parent / "fixtures" / "markets_kraken_fixture.json"
    out.write_text(json.dumps(k.fetch_markets(), indent=1, default=str) + "\n")


if __name__ == "__main__":
    main()
