"""Plain-text summaries of the results files."""
from __future__ import annotations

from collections import Counter


def _pct(x):
    return "n/a" if x is None else f"{x * 100:+.3f}%"


def insample_markdown(out: dict) -> str:
    lines = ["# In-sample results", "",
             f"Evaluation window: {out['evaluation_start'][:10]} to {out['holdout_start'][:10]} "
             "(the sealed final year is not included).", "",
             "Verdicts come only from the **primary universe (BTC/USD, ETH/USD) at base fees**. "
             "Other rows are supporting evidence.", ""]
    for run in out["runs"]:
        bh = run["benchmark_equal_weight_buy_and_hold"]
        lines += [f"## {run['universe']} universe, {run['scenario']} fees", "",
                  f"Reality-check p-value (family-wise, not a gate): {run['reality_check_pvalue']:.3f}. "
                  f"Equal-weight buy-and-hold: mean daily {_pct(bh['mean_daily'])}, "
                  f"Sharpe {bh['sharpe_annual']:.2f}.", "",
                  "| Config | Trades | Mean daily | 95% lower bound | Sharpe | Beats nulls | Mean R/trade | Verdict |",
                  "| --- | --- | --- | --- | --- | --- | --- | --- |"]
        for cid, c in sorted(run["configs"].items()):
            mr = "n/a" if c["mean_r_per_trade"] is None else f"{c['mean_r_per_trade']:+.2f}R"
            lines.append(f"| {cid} | {c['trades']} | {_pct(c['mean_daily'])} | "
                         f"{_pct(c['lower_bound_daily'])} | {c['sharpe_annual']:.2f} | "
                         f"{c['null_percentile'] * 100:.0f}% | {mr} | {c['verdict']} |")
        lines.append("")
    return "\n".join(lines)


def verdict_summary(out: dict) -> str:
    run = next(r for r in out["runs"] if r["universe"] == "primary" and r["scenario"] == "base")
    counts = Counter(c["verdict"] for c in run["configs"].values())
    return ", ".join(f"{k}: {v}" for k, v in sorted(counts.items()))
