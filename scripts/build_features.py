
"""
Build monthly stock returns for large-cap names only (MktCap > 10B).
Inputs:
- data/raw/Monthly_Data.csv   (date, iShares, NR1..NRn)
- data/raw/Basic_Data.csv     (NR, MarketCap, ...)

Outputs:
- data/processed/stock_returns_wide.csv  (date + one column per NR with 1m returns)
- data/processed/stock_returns_long.csv  (date, NR, ret_1m)
"""

from pathlib import Path
import sys
from pathlib import Path as _P

# Ensure we can import from src/
sys.path.insert(0, str(_P(__file__).resolve().parents[1] / "src"))

import pandas as pd
from momentum.data_io import load_monthly_data, load_basic_data

OUT = Path("data/processed")
OUT.mkdir(parents=True, exist_ok=True)


def _find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """
    Return the first matching column name (case-insensitive, trimmed) from candidates.
    Handles headers with leading/trailing spaces like ' Company Market Capitalization '.
    """
    # map "normalized" -> original
    norm2orig = {str(c).strip().lower(): c for c in df.columns}
    for cand in candidates:
        key = cand.strip().lower()
        if key in norm2orig:
            return norm2orig[key]
    return None


def _to_float_series(s: pd.Series) -> pd.Series:
    """Coerce market cap strings like '1,234,567,890' to float; keep NaN on failure."""
    return (
        s.astype(str)
         .str.replace(r"[^\d.\-eE]", "", regex=True)  # drop spaces/commas/currency symbols
         .replace({"": None})
         .astype(float)
    )


def main() -> None:
    # 1) Load data
    monthly = load_monthly_data().copy()
    monthly = monthly.sort_values("date")  # 'date' already parsed in data_io
    basic = load_basic_data().copy()

    # 2) Identify key columns
    date_col = "date"
    bench_col = monthly.columns[1]             # e.g., 'iShares' (ignored here)
    all_stock_cols = list(monthly.columns[2:]) # NR columns

    # 3) Resolve linking + market cap columns from Basic_Data (robust to naming)
    nr_col = _find_column(basic, ["NR", "Nr", "Id", "ID", "Ticker", "Symbol"])
    mcap_col = _find_column(
        basic,
        [
            "MktCap",
            "MarketCap",
            "Market Cap",
            "Company Market Capitalization",
            "Company Market Capitalization (Local)",
            "Market Capitalization",
        ],
    )

    if nr_col is None or mcap_col is None:
        raise ValueError(
            f"Could not find linking or market cap column. "
            f"Found NR-like: {nr_col}, MktCap-like: {mcap_col}. "
            f"Available columns: {list(basic.columns)}"
        )

    # 4) Build eligible universe: MktCap > 10B
    # Normalize & parse
    basic[nr_col] = basic[nr_col].astype(str).str.strip()
    basic[mcap_col] = _to_float_series(basic[mcap_col])

    eligible_ids = set(basic.loc[basic[mcap_col] > 10_000_000_000, nr_col].tolist())

    # Intersect with columns actually present in Monthly_Data
    stock_cols = [c for c in all_stock_cols if str(c) in eligible_ids]

    if len(stock_cols) == 0:
        raise ValueError(
            "No overlap between eligible large-cap NR codes and Monthly_Data columns. "
            f"Eligible IDs (sample): {list(sorted(eligible_ids))[:10]}"
        )

    print(f"✅ Keeping {len(stock_cols)} large-cap stocks (MktCap > 10B).")
    print(f"ℹ️  Dropped {len(all_stock_cols) - len(stock_cols)} smaller-cap/absent columns.")

    # 5) Ensure numeric for selected stocks
    monthly[stock_cols] = monthly[stock_cols].apply(pd.to_numeric, errors="coerce")

    # 6) Compute monthly returns (pct_change) for each selected stock
    rets_wide = monthly[[date_col] + stock_cols].copy()
    rets_wide[stock_cols] = rets_wide[stock_cols].pct_change(fill_method=None)  # no pad

    # 7) Save wide
    out_wide = OUT / "stock_returns_wide.csv"
    rets_wide.to_csv(out_wide, index=False)

    # 8) Long format (date, NR, ret_1m) with basic sanity filter
    rets_long = rets_wide.melt(id_vars=date_col, var_name="NR", value_name="ret_1m")
    rets_long = rets_long.dropna(subset=["ret_1m"])
    rets_long = rets_long[(rets_long["ret_1m"] > -2.0) & (rets_long["ret_1m"] < 2.0)]

    out_long = OUT / "stock_returns_long.csv"
    rets_long.to_csv(out_long, index=False)

    # 9) Quick summary
    print("✅ Built monthly returns for large-caps")
    print("  →", out_wide)
    print("  →", out_long)
    print("Rows (long):", len(rets_long))
    print("Dates:", rets_long["date"].min(), "→", rets_long["date"].max())
    print("Sample:", rets_long.head(5).to_string(index=False))


if __name__ == "__main__":
    main()