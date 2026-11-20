"""Command line for the study. Each step reads and writes files, so CI can run them separately.

  python -m study.cli backtest  --phase insample   # 18 configs x 3 fee scenarios x 2 universes
  python -m study.cli bias                          # Freqtrade look-ahead checks (fails on bias)
  python -m study.cli evaluate                      # verdicts -> results/insample.json + .md
  python -m study.cli holdout                       # ONLY after in-sample results are committed
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from study import evaluate as E
from study import report
from study import run as R
from study.stats import holdout_floor, final_verdict, returns, daily_equity

ROOT = Path(__file__).resolve().parent.parent


def manifest(path: Path) -> dict:
    return json.loads(path.read_text())


def common_start(datadir: Path, warmup_days: int = 250) -> pd.Timestamp:
    """First BTC day plus the longest warm-up, so every configuration is scored on the same days."""
    closes = E.load_closes(datadir, ["BTC/USD"])
    return closes.index[0] + pd.Timedelta(days=warmup_days)


def cmd_backtest(args) -> None:
    m = manifest(Path(args.manifest))
    holdout_start = pd.Timestamp(m["holdout_start"])
    datadir = Path(args.datadir) / "insample"
    start = common_start(datadir)
    timerange = f"{start:%Y%m%d}-{holdout_start:%Y%m%d}"
    specs = R.expand(R.load_grid(), args.scenario or None, args.universe or None)
    for i, spec in enumerate(specs, 1):
        R.run_backtest(spec, datadir, Path(args.markets), Path(args.runs), timerange)
        print(f"[{i}/{len(specs)}] {spec.run_id}", flush=True)


def cmd_bias(args) -> None:
    """Look-ahead check on the middle parameter of each family and timeframe; fails on any bias."""
    m = manifest(Path(args.manifest))
    holdout_start = pd.Timestamp(m["holdout_start"])
    datadir = Path(args.datadir) / "insample"
    start = common_start(datadir)
    grid = R.load_grid()
    checks = []
    for family, f in grid["families"].items():
        middle = f["values"][len(f["values"]) // 2]
        for spec in R.expand(grid, ["base"], ["primary"]):
            if spec.family == family and spec.value == middle:
                checks.append(R.run_bias_checks(spec, datadir, Path(args.markets), Path(args.runs),
                                                f"{start:%Y%m%d}-{holdout_start:%Y%m%d}"))
    E.save({"lookahead": checks}, Path(args.out) / "bias_checks.json")
    print(json.dumps(checks, indent=1))
    if any(c["has_bias"] is not False for c in checks):
        raise SystemExit("Look-ahead check found bias or could not run: stop and report")


def cmd_evaluate(args) -> None:
    m = manifest(Path(args.manifest))
    holdout_start = pd.Timestamp(m["holdout_start"])
    datadir = Path(args.datadir) / "insample"
    start = common_start(datadir)
    grid = R.load_grid()
    btc = E.load_closes(datadir, ["BTC/USD"])["BTC/USD"]
    out = {"holdout_start": m["holdout_start"], "evaluation_start": start.isoformat(), "runs": []}
    for universe, u in grid["universes"].items():
        closes = E.load_closes(datadir, u["pairs"])
        for scenario in grid["fee_scenarios"]:
            specs = [s for s in R.expand(grid, [scenario], [universe])]
            results = {s: R.load_trades(Path(args.runs) / s.run_id / "results") for s in specs}
            out["runs"].append(E.evaluate_universe(results, closes, btc, start, holdout_start,
                                                   universe, scenario))
    E.save(out, Path(args.out) / "insample.json")
    (Path(args.out) / "insample.md").write_text(report.insample_markdown(out))
    print(report.verdict_summary(out))


def cmd_holdout(args) -> None:
    """Score the sealed final year, once, for configurations that passed in-sample."""
    insample = json.loads((Path(args.out) / "insample.json").read_text())
    m = manifest(Path(args.manifest))
    holdout_start, data_end = pd.Timestamp(m["holdout_start"]), pd.Timestamp(m["data_end_exclusive"])
    full = Path(args.datadir) / "sealed_full"
    grid = R.load_grid()
    primary = next(r for r in insample["runs"]
                   if r["universe"] == E.VERDICT_UNIVERSE and r["scenario"] == E.VERDICT_SCENARIO)
    specs = {s.config_id: s for s in R.expand(grid, [E.VERDICT_SCENARIO], [E.VERDICT_UNIVERSE])}
    closes_full = E.load_closes(full, grid["universes"][E.VERDICT_UNIVERSE]["pairs"])
    in_dir = Path(args.datadir) / "insample"
    closes_in = E.load_closes(in_dir, grid["universes"][E.VERDICT_UNIVERSE]["pairs"])
    in_days = E.evaluation_days(closes_in, pd.Timestamp(insample["evaluation_start"]), holdout_start)
    ho_days = E.evaluation_days(closes_full, holdout_start, data_end)
    result = {"holdout_window": [holdout_start.isoformat(), data_end.isoformat()], "configs": {}}
    for cid, row in primary["configs"].items():
        entry = {"in_sample_verdict": row["verdict"]}
        if row["verdict"] == "PASS_INSAMPLE":
            spec = specs[cid]
            in_trades = R.load_trades(Path(args.runs) / spec.run_id / "results")
            in_r = returns(daily_equity(in_trades, closes_in, E.START_BALANCE, in_days))
            rng = np.random.default_rng(E.seed_for("holdout-" + cid))
            floor = holdout_floor(in_r.to_numpy(), rng)
            res_dir = R.run_backtest(spec, full, Path(args.markets), Path(args.runs) / "holdout",
                                     f"{holdout_start:%Y%m%d}-{data_end:%Y%m%d}")
            ho_trades = R.load_trades(res_dir)
            ho_trades = ho_trades[ho_trades["open_date"] >= holdout_start]
            ho_r = returns(daily_equity(ho_trades, closes_full, E.START_BALANCE, ho_days))
            entry.update(holdout_mean_daily=float(ho_r.mean()), holdout_floor=floor,
                         holdout_trades=int(len(ho_trades)))
            entry["final_verdict"] = final_verdict(row["verdict"], entry["holdout_mean_daily"], floor)
        else:
            entry["final_verdict"] = final_verdict(row["verdict"], None, None)
        result["configs"][cid] = entry
    E.save(result, Path(args.out) / "holdout.json")
    print(json.dumps({k: v["final_verdict"] for k, v in result["configs"].items()}, indent=1))


def main(argv=None) -> None:
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=["backtest", "bias", "evaluate", "holdout"])
    p.add_argument("--manifest", default=str(ROOT / "data" / "manifest.json"))
    p.add_argument("--markets", default=str(ROOT / "data" / "markets_kraken.json"))
    p.add_argument("--datadir", default=str(ROOT / "user_data" / "data"))
    p.add_argument("--runs", default=str(ROOT / "runs"))
    p.add_argument("--out", default=str(ROOT / "results"))
    p.add_argument("--scenario", action="append")
    p.add_argument("--universe", action="append")
    args = p.parse_args(argv)
    {"backtest": cmd_backtest, "bias": cmd_bias, "evaluate": cmd_evaluate,
     "holdout": cmd_holdout}[args.command](args)


if __name__ == "__main__":
    main()
