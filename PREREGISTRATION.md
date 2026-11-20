# Pre-registration: BTC/ETH edge feasibility study

**Written 2026-11-20, before any real market data was downloaded or any backtest was run on real data.** The git commit that adds this file is the timestamp. Everything below is fixed before results exist. Any change before results gets a dated entry under [Amendments](#amendments). Nothing changes after results exist.

The frozen files are listed with their SHA-256 hashes in `PREREGISTRATION.lock`. The test suite fails if any of them changes without the lock being updated in the same commit.

## Question

Does any simple, pre-registered long-only strategy on BTC/USD and ETH/USD, on 4-hour or daily bars, make money after Kraken's retail fees, in a way that random timing does not?

## Owner decisions (2026-11-20)

- 4-hour and daily strategies only. Positions may stay open overnight.
- Kraken is the venue whose fees we model. Starting equity $500. Spot only, long only, no leverage.
- Running costs are capped at $10 a month until any real-money trading.
- Results are judged on daily net returns over all available history. Other coins count as extra evidence only.
- Every configuration gets one verdict: pass, fail or inconclusive.

## Data

- **Source: Coinbase Exchange public 1-hour candles, fetched through CCXT, from the earliest available hour.** That is about mid-2015 for BTC and mid-2016 for ETH.
  - **Why not Kraken.** Kraken's public API serves only the last 720 candles. Rebuilding ten years from Kraken's raw trade history isn't practical on free GitHub runners. Coinbase is a large USD spot venue, and BTC and ETH prices across major USD venues differ far less than the fees modelled here. *This differs from the original plan's "Kraken history" and is flagged for the owner.*
- **Bars:** 1-hour candles resampled to UTC-aligned 4-hour and daily bars. A bar with no trades at all is left missing, and Freqtrade fills it flat.
- **Pairs.** Primary: BTC/USD and ETH/USD. Supporting evidence only: LTC, LINK, XRP, ADA, SOL and DOT against USD.
- **Sealed holdout:** the 365 days before the UTC day of the download. Holdout candles are written only to a separate directory (`sealed_full`), and every in-sample backtest reads a directory that does not contain them. A test checks this.
- **Provenance:** `data/manifest.json` records the source, the retrieval time, the CCXT version, the gap counts and the SHA-256 of a canonical CSV of each pair's in-sample and holdout candles. Raw data is not committed to git.
- **Quality stop:** if more than 1% of hours are missing from BTC/USD or ETH/USD in-sample, the study stops and reports.

## Account and execution rules (all configurations)

- **Starting equity and pairs:** $500, with at most one open position per pair, so at most 2 at once in the primary universe.
- **Sizing:** each trade risks 1% of current equity to its stop. Quantity is 1% of equity divided by the stop distance, capped at available cash (no leverage). Fees aren't in the risk budget.
- **Stop:** fixed at entry, at the entry price minus *k* × ATR(14) of the signal bar. *k* depends on the family. In the backtest, a stop fills at the stop price, or at the bar's open if the bar opens beyond the stop (gap).
- **Orders:** market orders at the next bar's open after a signal.
- **Fee scenarios (per side, applied to both legs):**

| Scenario | Fee per side | Meaning | Role |
| --- | --- | --- | --- |
| base | 0.85% | Kraken tier-1 taker (0.80%) + 0.05% spread and slippage | **Verdicts** |
| optimistic | 0.65% | Maker entry plus taker exit, or tier-2 taker, + 0.05% | Evidence |
| gross | 0% | No costs | Diagnostic only: how much fees take |

## Hypotheses and grid (18 configurations)

The parameter values are common textbook choices, set before seeing this data. They aren't tuned. The grid is `config/grid.json`.

| Family | Rule | Stop | Expected sign | Values | Timeframes |
| --- | --- | --- | --- | --- | --- |
| **H1 TrendDonchian** | Enter when the close is above the prior *n*-bar high. Exit when the close is below the prior *n*/2-bar low | 3 × ATR | Positive (time-series momentum) | n = 20, 55, 100 | 4h, 1d |
| **H2 VolBreakout** | Enter when the close is more than *m* × ATR(14) above the previous close. Exit after 10 bars | 2 × ATR | Positive (volatility expansion continues) | m = 1.0, 1.5, 2.0 | 4h, 1d |
| **H3 MeanReversion** (control) | Enter when RSI(2) is below the threshold and the close is above SMA(200). Exit when the close is above SMA(5), or after 5 bars | 3 × ATR | Gross edge possible; **expected to fail after fees** | threshold = 5, 10, 20 | 4h, 1d |

## Evaluation

**Window.** Every configuration is scored on the same days: from the first BTC day plus 250 days of indicator warm-up, to the start of the holdout. No parameters are fitted, so each configuration is scored once on all pre-holdout data. The earlier plan's word "walk-forward" therefore reduces to this single out-of-tuning pass.

**Primary series.** The daily net return of marked-to-market equity, at the end of each UTC day. Open positions are marked at the daily close, net of the entry fee. Closed trades count at their realised profit, net of both fees.

**Verdict population.** Only the **primary universe (BTC/USD, ETH/USD) at base fees** gets verdicts. Optimistic fees, gross results and the six supporting coins are reported as evidence and never change a verdict.

### Gates

A configuration is **PASS_INSAMPLE** only if all three hold:

1. **Profit with 95% confidence.** The 5th percentile of 10,000 circular-block-bootstrap means of daily net returns (20-day blocks) is above 0. This is a one-sided 95% lower bound.
2. **Better than random timing.** The configuration's mean daily return under the exposure model beats at least 95% of 1,000 timing-shift nulls.
    - *Exposure model:* yesterday's exposure × today's asset return, minus the fee rate × the traded fraction.
    - *Nulls:* the same configuration's own daily exposure series, circularly shifted by a random 30 days or more against asset returns, with the same fee. Each null keeps the exposure, turnover and holding periods exactly. Only the timing changes.
3. **Enough trades:** at least 50 in-sample, as a sanity floor only.

Otherwise the verdict is **FAIL** if the mean daily net return is 0 or below, or if it beats fewer than 50% of nulls. Anything else is **INCONCLUSIVE**.

### Holdout (gate 4, run once)

- **Who and when:** this runs only after the in-sample results are committed, and only for configurations that are PASS_INSAMPLE.
- **The test:** each such configuration is backtested on the sealed year with unchanged code and parameters.
- **The verdict:** **PASS** if its mean daily net return is at least the 5th percentile of 10,000 block-bootstrapped 365-day means drawn from its own in-sample days. Otherwise **FAIL**.
- **No reuse:** the holdout is never used again.

INCONCLUSIVE and FAIL mean no money is committed.

### Reported, not gates

- **Family-wise reality-check p-value:** how often the best of the 18 shifted configurations beats the best real configuration. It uses the same shifts for all 18.
- **Per configuration:** net R per trade, results by calendar year, and bull/bear regime splits. A bull day is one where BTC closed above its 200-day average the day before.
- **Benchmark:** equal-weight buy-and-hold over the same window.

### Bias checks

- **Freqtrade `lookahead-analysis`:** runs on the middle parameter of each family and timeframe. **Any detected bias stops the study.** Freqtrade `recursive-analysis` runs alongside, and its output is kept for review.
- **Unit tests:** they check that signals are unchanged when future bars are removed.

## Failure conditions (stop and report; don't improvise)

- More than 1% missing hours in BTC/ETH in-sample data.
- Freqtrade can't apply the 1%-risk sizing with ATR stops. A test checks this: planned risk is about $5.00 on the first trade, and never above 1% of equity plus 10% headroom.
- Look-ahead bias is detected and can't be explained.
- The work passes 40 hours.

## After the verdicts

- **Any PASS:** a phase 2 paper-trading proposal goes to the owner for approval.
- **No PASS:** a written "no".
- **At most one further round:** three new families, pre-registered the same way, with **no reuse of this holdout**.

## Amendments

None yet.
