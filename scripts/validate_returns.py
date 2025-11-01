
"""This script validates the processed stock returns against the raw levels data.
It performs several checks:
1) Ensures the benchmark column is not included in the stock returns.
2) Recomputes returns for a random sample of tickers and compares to processed returns.
3) Checks for exactly one leading NaN per ticker in the wide returns format.
4) Examines the distribution of returns for reasonableness.
5) Validates consistency between wide and long returns formats by reconstructing one from the other.
"""


import sys
from pathlib import Path
proj_root = Path(__file__).resolve().parents[1]
# Prefer the src layout, but also add the project root as a fallback so
# the momentum package can be discovered in either location.
sys.path.insert(0, str(proj_root / "src"))
sys.path.insert(0, str(proj_root))

import random
import pandas as pd
from momentum.data_io import load_monthly_data

PROC = Path("data/processed")


def _to_dt(s: pd.Series) -> pd.Series:
    """Parse dates robustly: try ISO first (YYYY-MM-DD), then day-first."""
    dt = pd.to_datetime(s, errors="coerce")
    if dt.isna().mean() > 0.3:
        dt = pd.to_datetime(s, errors="coerce", dayfirst=True)
    return dt


def main():
    """Run validations on processed stock returns data."""
    levels = load_monthly_data().copy()
    levels["date"] = _to_dt(levels["date"])
    levels = levels.sort_values("date")

    bench_col = levels.columns[1]      # e.g., 'iShares'
    stock_cols = list(levels.columns[2:])

    rets_wide = pd.read_csv(PROC / "stock_returns_wide.csv")
    rets_wide["date"] = _to_dt(rets_wide["date"])
    rets_wide = rets_wide.sort_values("date")

    rets_long = pd.read_csv(PROC / "stock_returns_long.csv")
    rets_long["date"] = _to_dt(rets_long["date"])
    rets_long = rets_long.sort_values("date")

    print("Levels:", levels.shape, "| Returns wide:", rets_wide.shape,
     "| Returns long:", rets_long.shape)

    # 1) Ensure benchmark not included in returns
    assert bench_col not in rets_wide.columns, f"Benchmark column {bench_col} leaked into returns!"

    # 2) Spot-check math on a few random tickers
    rng = random.Random(42)
    sample = list(rng.sample(stock_cols, k=min(5, len(stock_cols))))

    # Convert only sampled columns to numeric (keep date intact)
    levels_num = levels[["date"] + sample].copy()
    levels_num[sample] = levels_num[sample].apply(pd.to_numeric, errors="coerce")

    manual = levels_num.copy()
    # Avoid deprecation warning by disabling fill
    manual[sample] = manual[sample].pct_change(fill_method=None)

    left = rets_wide[["date"] + sample].copy()
    merged = left.merge(manual, on="date", suffixes=("_built", "_manual"))

    diffs = {
        tkr: (merged[f"{tkr}_built"] - merged[f"{tkr}_manual"]).abs().max()
        for tkr in sample
    }
    print("Max abs diff (built vs manual pct_change) per sampled ticker:", diffs)

    # 3) NaNs per ticker (expect ≈1 lead NaN)
    nan_counts = rets_wide.drop(columns=["date"]).isna().sum()
    print("Median NaNs per ticker (expect ≈1):", float(nan_counts.median()))
    print("Tickers with >3 NaNs (inspect):", int((nan_counts > 3).sum()))

    # 4) Reasonable return ranges
    q = rets_long["ret_1m"].quantile([0.001, 0.01, 0.99, 0.999])
    print("Return quantiles:\n", q.to_string())
    extreme = rets_long[(rets_long["ret_1m"] <= -2.0) | (rets_long["ret_1m"] >= 2.0)]
    print("Extreme moves (|r| >= 200%):", len(extreme))

    # 5) Wide vs long consistency (pivot long back to wide and compare)
    pivot = rets_long.pivot(index="date", columns="NR", values="ret_1m").reset_index()

    # Only compare NR columns common to both (exclude 'date' itself)
    nr_cols_common = [c for c in pivot.columns if c != "date" and c in rets_wide.columns]
    common_cols = ["date"] + nr_cols_common

    m2 = rets_wide[common_cols].merge(
        pivot[common_cols], on="date", suffixes=("_built", "_pivot")
    )

    maxdiff = 0.0
    for c in nr_cols_common:
        d = (m2[f"{c}_built"] - m2[f"{c}_pivot"]).abs().max(skipna=True)
        if pd.notna(d):
            maxdiff = max(maxdiff, float(d))
    print("Max wide vs long reconstruction diff:", maxdiff)

    print("\n✅ Validation finished. If diffs ≈ 0 and ranges look sane, returns are OK.")


if __name__ == "__main__":
    main()
