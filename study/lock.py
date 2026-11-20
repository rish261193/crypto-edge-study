"""Write PREREGISTRATION.lock: SHA-256 of every file the pre-registration freezes.

Run only together with a dated amendment in PREREGISTRATION.md, before results exist."""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FROZEN = ["PREREGISTRATION.md", "config/grid.json", "config/base.json", "study/stats.py",
          "study/evaluate.py", "user_data/strategies/study_base.py",
          "user_data/strategies/trend_donchian.py", "user_data/strategies/vol_breakout.py",
          "user_data/strategies/mean_reversion.py"]


def main() -> None:
    lines = ["# sha256  path  (see PREREGISTRATION.md; regenerate only with an amendment)"]
    for rel in FROZEN:
        lines.append(f"{hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()}  {rel}")
    (ROOT / "PREREGISTRATION.lock").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
