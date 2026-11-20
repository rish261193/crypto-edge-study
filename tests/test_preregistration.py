"""The pre-registered files must match PREREGISTRATION.lock; the grid must match the document."""
import hashlib
import json
from pathlib import Path

from study import run as R
from study import stats as S

ROOT = Path(__file__).resolve().parent.parent


def lock_entries():
    for line in (ROOT / "PREREGISTRATION.lock").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            digest, path = line.split(maxsplit=1)
            yield digest, path


def test_frozen_files_match_lock():
    for digest, path in lock_entries():
        actual = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        assert actual == digest, f"{path} changed after pre-registration; add an amendment and update the lock"


def test_lock_covers_grid_strategies_and_stats():
    paths = {p for _, p in lock_entries()}
    assert {"config/grid.json", "study/stats.py", "user_data/strategies/study_base.py",
            "user_data/strategies/trend_donchian.py", "user_data/strategies/vol_breakout.py",
            "user_data/strategies/mean_reversion.py", "PREREGISTRATION.md"} <= paths


def test_grid_has_18_configurations_and_three_fee_scenarios():
    grid = R.load_grid()
    configs = {s.config_id for s in R.expand(grid)}
    assert len(configs) == 18
    assert grid["fee_scenarios"] == {"base": 0.0085, "optimistic": 0.0065, "gross": 0.0}
    assert grid["universes"]["primary"]["pairs"] == ["BTC/USD", "ETH/USD"]


def test_stats_constants_match_document():
    text = (ROOT / "PREREGISTRATION.md").read_text()
    assert S.BLOCK_DAYS == 20 and "20-day blocks" in text
    assert S.N_BOOTSTRAP == 10_000 and "10,000" in text
    assert S.N_NULLS == 1_000 and "1,000 timing-shift nulls" in text
    assert S.MIN_TRADES == 50 and "at least 50 in-sample" in text
    assert S.NULL_PERCENTILE_GATE == 0.95 and S.LOWER_QUANTILE == 0.05
    assert S.MIN_SHIFT_DAYS == 30 and "30 days or more" in text


def test_base_config_is_paper_only():
    cfg = json.loads((ROOT / "config" / "base.json").read_text())
    assert cfg["dry_run"] is True and cfg["trading_mode"] == "spot"
    assert cfg["exchange"]["key"] == "" and cfg["exchange"]["secret"] == ""
    assert cfg["dry_run_wallet"] == 500 and cfg["force_entry_enable"] is False
