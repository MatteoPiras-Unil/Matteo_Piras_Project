# scripts/compute_metrics.py
from __future__ import annotations
import sys
import argparse
from pathlib import Path
from pathlib import Path as _P

# Make src importable when running "python scripts/compute_metrics.py"
sys.path.insert(0, str(_P(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd

from momentum.metrics import metrics_table, align_common_start
from momentum.data_io import load_monthly_data  # to rebuild benchmark

DATA = Path("data/processed")
RES = Path("results")
RES.mkdir(parents=True, exist_ok=True)

PORT_SIZES = [10, 20, 30, 40, 50]


def load_portfolios() -> dict[str, pd.Series]:
    """Load Top N portfolio monthly returns as named Series indexed by datetime."""
    named: dict[str, pd.Series] = {}
    for n in PORT_SIZES:
        path = DATA / f"portfolio_returns_top{n}.csv"
        df = pd.read_csv(path)
        # Expect two columns: date, value
        df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], errors="coerce")
        s = pd.to_numeric(df.iloc[:, 1], errors="coerce")
        s.index = df.iloc[:, 0]
        s.name = f"Top {n}"
        named[s.name] = s.sort_index()
    return named


def load_benchmark_returns() -> pd.Series:
    """Build benchmark monthly returns from the raw levels (iShares column)."""
    levels = load_monthly_data().copy().sort_values("date")
    date_col = "date"
    bench_col = levels.columns[1]  # iShares / benchmark column
    levels[date_col] = pd.to_datetime(levels[date_col], errors="coerce")

    # Clean to numeric robustly (remove commas, spaces, stray chars)
    levels[bench_col] = (
        levels[bench_col]
        .astype(str)
        .str.replace(r"[^\d.\-eE]", "", regex=True)
        .replace(r"^\s*$", np.nan, regex=True)
    )
    levels[bench_col] = pd.to_numeric(levels[bench_col], errors="coerce")

    bench = levels[[date_col, bench_col]].dropna(subset=[bench_col]).copy()
    bench["bench_ret"] = bench[bench_col].pct_change(fill_method=None)
    bench = bench.dropna(subset=["bench_ret"]).set_index(date_col)["bench_ret"]
    bench.name = "Benchmark"
    return bench


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--lookback",
        type=int,
        default=6,
        choices=[1, 3, 6, 12],
        help="Momentum horizon label for saving (only affects output filename).",
    )
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    lookback = args.lookback

    # Load data
    portfolios = load_portfolios()
    bench = load_benchmark_returns()

    # Align everyone to a common start date
    portfolios_aligned, bench_aligned, common_start = align_common_start(portfolios, bench)
    print(f"Common start date for metrics: {common_start.date()}")

    # Build one dict including the benchmark for the table
    named_all = {**portfolios_aligned, "Benchmark": bench_aligned}

    # Compute metrics
    df = metrics_table(named_all)
    pd.set_option("display.float_format", lambda x: f"{x:0.4f}")
    print("\n=== Performance Metrics (aligned sample) ===")
    print(df)

    # Save with horizon-specific suffix (normalize 6m to _6m as well)
    suffix = f"_{lookback}m"
    out = RES / f"metrics_summary{suffix}.csv"
    df.to_csv(out, index=True)
    print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()

