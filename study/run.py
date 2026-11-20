"""Run every pre-registered Freqtrade backtest and collect the trade lists."""
from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class RunSpec:
    family: str
    param: str
    value: float
    timeframe: str
    scenario: str
    fee: float
    universe: str
    pairs: tuple[str, ...]
    max_open_trades: int

    @property
    def config_id(self) -> str:
        return f"{self.family}-{self.param}{self.value:g}-{self.timeframe}"

    @property
    def run_id(self) -> str:
        return f"{self.config_id}-{self.universe}-{self.scenario}"


def load_grid(path: Path = ROOT / "config" / "grid.json") -> dict:
    return json.loads(path.read_text())


def expand(grid: dict, scenarios: list[str] | None = None,
           universes: list[str] | None = None) -> list[RunSpec]:
    specs = []
    for family, f in grid["families"].items():
        for value in f["values"]:
            for tf in grid["timeframes"]:
                for sc, fee in grid["fee_scenarios"].items():
                    if scenarios and sc not in scenarios:
                        continue
                    for uni, u in grid["universes"].items():
                        if universes and uni not in universes:
                            continue
                        specs.append(RunSpec(family, f["param"], value, tf, sc, fee, uni,
                                             tuple(u["pairs"]), int(u["max_open_trades"])))
    return specs


def write_config(spec: RunSpec, datadir: Path, out: Path) -> Path:
    cfg = json.loads((ROOT / "config" / "base.json").read_text())
    cfg.pop("$comment", None)
    cfg["timeframe"] = spec.timeframe
    cfg["max_open_trades"] = spec.max_open_trades
    cfg["exchange"]["pair_whitelist"] = list(spec.pairs)
    cfg["study_params"] = {spec.param: spec.value}
    cfg["user_data_dir"] = str(ROOT / "user_data")
    cfg["strategy_path"] = str(ROOT / "user_data" / "strategies")
    out.mkdir(parents=True, exist_ok=True)
    path = out / "config.json"
    path.write_text(json.dumps(cfg, indent=1))
    return path


def run_backtest(spec: RunSpec, datadir: Path, markets: Path, out: Path,
                 timerange: str) -> Path:
    run_dir = out / spec.run_id
    cfg = write_config(spec, datadir, run_dir)
    cmd = [sys.executable, "-m", "study.ft_offline", str(markets), "backtesting",
           "--config", str(cfg), "--datadir", str(datadir), "--strategy", spec.family, "--timerange", timerange,
           "--fee", str(spec.fee), "--export", "trades", "--cache", "none",
           "--backtest-directory", str(run_dir / "results")]
    (run_dir / "results").mkdir(parents=True, exist_ok=True)
    log = run_dir / "freqtrade.log"
    with log.open("w") as fh:
        proc = subprocess.run(cmd, cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT)
    results = run_dir / "results"
    # Freqtrade exits 0 on configuration errors, so check for the result file too.
    if proc.returncode != 0 or not results.is_dir() or not any(results.glob("*.zip")):
        raise RuntimeError(f"Backtest {spec.run_id} failed; see {log}")
    return results


def load_trades(results_dir: Path):
    from freqtrade.data.btanalysis import load_backtest_data

    return load_backtest_data(results_dir)


def run_bias_checks(spec: RunSpec, datadir: Path, markets: Path, out: Path,
                    timerange: str) -> dict:
    """Freqtrade's look-ahead and recursive analyses for one configuration.

    Returns {"has_bias": bool | None, ...}. None means the check could not run."""
    import csv

    run_dir = out / f"bias-{spec.config_id}"
    cfg = write_config(spec, datadir, run_dir)
    export = run_dir / "lookahead.csv"
    base = [sys.executable, "-m", "study.ft_offline", str(markets)]
    common = ["--config", str(cfg), "--datadir", str(datadir), "--strategy", spec.family,
              "--timerange", timerange]
    with (run_dir / "lookahead.log").open("w") as fh:
        subprocess.run(base + ["lookahead-analysis", *common, "--fee", str(spec.fee),
                               "--backtest-directory", str(run_dir / "bt"),
                               "--lookahead-analysis-exportfilename", str(export)],
                       cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT)
    with (run_dir / "recursive.log").open("w") as fh:
        subprocess.run(base + ["recursive-analysis", *common, "--startup-candle", "199", "499"],
                       cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT)
    if not export.exists():
        return {"config": spec.config_id, "has_bias": None}
    with export.open() as fh:
        rows = [r for r in csv.DictReader(fh) if r.get("strategy") == spec.family]
    if not rows:
        return {"config": spec.config_id, "has_bias": None}
    row = rows[-1]
    return {"config": spec.config_id, "has_bias": row.get("has_bias", "").strip().lower() == "true",
            "total_signals": row.get("total_signals"),
            "biased_entry_signals": row.get("biased_entry_signals"),
            "biased_exit_signals": row.get("biased_exit_signals")}
