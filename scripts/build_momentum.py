"""
Compute MSCI-style 6-month Price Momentum:
    mom_6m(t) = (P_{t-1} / P_{t-7}) - 1
using monthly price levels, excluding the current month (t).

Steps:
1) Load monthly price levels and basic data (from src/momentum/data_io.py)
2) Identify columns: date, benchmark, stock NRs
3) Find NR and MarketCap columns in Basic_Data
4) Build large-cap universe (MktCap > $10B), intersect with columns in levels
5) Ensure numeric for the selected stocks
6) Compute momentum in wide format
7) Save wide format CSV
8) Convert to long format, drop NaNs and outliers, save CSV
9) Print summary statistics
"""

from __future__ import annotations
import sys
from pathlib import Path
from pathlib import Path as _P

# ensure we can import from src/
sys.path.insert(0, str(_P(__file__).resolve().parents[1] / "src"))

import pandas as pd
from momentum.data_io import load_monthly_data, load_basic_data

OUT = Path("data/processed")
OUT.mkdir(parents=True, exist_ok=True)


def _find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Return first matching column (case-insensitive, trimmed)."""
    norm2orig = {str(c).strip().lower(): c for c in df.columns}
    for cand in candidates:
        key = cand.strip().lower()
        if key in norm2orig:
            return norm2orig[key]
    return None


def _to_float_series(s: pd.Series) -> pd.Series:
    """Parse market cap strings like '1,234,567,890' to float."""
    return (
        s.astype(str)
         .str.replace(r"[^\d.\-eE]", "", regex=True)
         .replace({"": None})
         .astype(float)
    )


def main() -> None:
    # 1) Load price levels and basics
    levels = load_monthly_data().copy()  # columns: date, benchmark, NR...
    levels = levels.sort_values("date")
    basic = load_basic_data().copy()

    # 2) Identify columns
    date_col = "date"
    bench_col = levels.columns[1]          # e.g., 'iShares' (we ignore for momentum)
    all_stock_cols = list(levels.columns[2:])

    # 3) Find NR + MarketCap columns in Basic_Data
    nr_col = "NR"
    mcap_col = " Company Market Capitalization "
    
    if nr_col is None or mcap_col is None:
        raise ValueError(
            f"Could not find NR or MarketCap columns in Basic_Data. "
            f"NR: {nr_col}, MktCap: {mcap_col}. Headers: {list(basic.columns)}"
        )

    # 4) Build large-cap universe (MktCap > $10B), intersect with columns in levels
    basic[nr_col] = basic[nr_col].astype(str).str.strip()
    basic[mcap_col] = _to_float_series(basic[mcap_col])
    eligible_ids = set(basic.loc[basic[mcap_col] > 10_000_000_000, nr_col].tolist())
    stock_cols = [c for c in all_stock_cols if str(c) in eligible_ids]

    if not stock_cols:
        raise ValueError("No overlap between >$10B universe and Monthly_Data columns.")

    print(f"✅ Large-cap universe: {len(stock_cols)} stocks (MktCap > $10B).")

    # 5) Ensure numeric for the selected stocks
    levels[stock_cols] = levels[stock_cols].apply(pd.to_numeric, errors="coerce")

    # 6) Compute MSCI 6-month momentum: (P_{t-1} / P_{t-7}) - 1
    # Excludes current month by using shift(1) in numerator.
    # Requires at least 7 months of history → first valid value appears at row index 7 (0-based).
    mom_wide = levels[[date_col] + stock_cols].copy()
    mom_wide[stock_cols] = (mom_wide[stock_cols].shift(1) / mom_wide[stock_cols].shift(7)) - 1

    # 7) Save wide
    out_wide = OUT / "momentum_wide.csv"
    mom_wide.to_csv(out_wide, index=False)

    # 8) Long format (date, NR, mom_6m), drop NaNs and outliers if any
    mom_long = mom_wide.melt(id_vars=date_col, var_name="NR", value_name="mom_6m")
    mom_long = mom_long.dropna(subset=["mom_6m"])
    # optional sanity guard
    mom_long = mom_long[(mom_long["mom_6m"] > -2.0) & (mom_long["mom_6m"] < 2.0)]

    out_long = OUT / "momentum_long.csv"
    mom_long.to_csv(out_long, index=False)

    # 9) Quick summary
    print("✅ Built MSCI 6m momentum")
    print("  →", out_wide)
    print("  →", out_long)
    print("Rows (long):", len(mom_long))
    print("Dates:", mom_long[date_col].min(), "→", mom_long[date_col].max())
    print("Sample:", mom_long.head(5).to_string(index=False))


if __name__ == "__main__":
    main()
