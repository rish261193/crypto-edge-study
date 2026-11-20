# crypto-edge-study

**Question:** can a simple, pre-registered long-only strategy on BTC/USD and ETH/USD (4-hour or daily bars) make money after Kraken's retail fees, in a way random timing can't?

This repo is the evidence. It is not a trading bot. Nothing here holds exchange keys or places orders. Every run is a paper backtest.

| Status | |
| --- | --- |
| Pre-registration | [PREREGISTRATION.md](PREREGISTRATION.md), frozen by [PREREGISTRATION.lock](PREREGISTRATION.lock) |
| In-sample results | Not run yet |
| Sealed holdout (final 365 days) | Not opened |

## How it works

1. **Data.** `study/data.py` downloads Coinbase 1-hour candles for BTC, ETH and six supporting coins. It resamples them to 4-hour and daily bars and seals the last 365 days in a separate directory. It writes `data/manifest.json` with gap counts and SHA-256 hashes. Raw data is never committed.
2. **Backtests.** [Freqtrade](https://www.freqtrade.io/) 2026.10 runs 3 strategy families × 3 parameter values × 2 timeframes = 18 configurations. Each runs under 3 fee scenarios and 2 coin universes.
    - **Rules:** every trade risks 1% of equity to an ATR stop, with Kraken tier-1 fees.
    - **Offline runs:** `study/ft_offline.py` makes runs reproducible by loading a saved snapshot of Kraken's market list instead of calling the exchange.
3. **Scoring.** `study/stats.py` scores daily net returns. It applies a one-sided 95% block-bootstrap bound and compares each configuration against 1,000 timing-shifted copies of itself. Each configuration gets **PASS**, **FAIL** or **INCONCLUSIVE** by the rules fixed in the pre-registration.
4. **Holdout.** The sealed year is scored **once**, only for configurations that passed in-sample.

## Running it

Everything runs in GitHub Actions on standard runners, which are free for public repos:

- **`tests`** runs on every push.
- **`in-sample study`** is manual. It downloads the data, runs the bias checks, the 108 backtests and the scoring, then commits `results/`. It refuses to run twice.
- **`holdout (run once)`** is manual. Its input is the run ID of the study run, and it refuses to run twice.

Locally (Python 3.13):

```
pip install -r requirements-lock.txt
python -m pytest -q
```

## Rules this repo follows

- **Nothing is changed after results exist.** Changes before then need a dated amendment in the pre-registration and a regenerated lock (`python -m study.lock`).
- **Every configuration is reported,** not only the winners.
- **The holdout is opened once.**
- **No exchange keys, ever.** The Freqtrade config is dry-run and spot only, with an empty key and secret.

## Licence

GPLv3, matching Freqtrade, which this project uses. This is not financial advice.
