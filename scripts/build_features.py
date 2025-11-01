# scripts/build_features.py
"""
Build monthly stock returns from Monthly_Data.csv.
Outputs:
- data/processed/stock_returns_long.csv  (date, NR, ret_1m)
- data/processed/stock_returns_wide.csv  (date + one column per NR with ret_1m)
"""

from pathlib import Path
import sys
from pathlib import Path as _P

# Make sure we can import from src/
sys.path.insert(0, str(_P(__file__).resolve().parents[1] / "src"))

import pandas as pd
from momentum.data_io import load_monthly_data

OUT = Path("data/processed")
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    # 1) Load monthly “levels” (date, iShares, NR1..NRn)
    monthly = load_monthly_data().copy()
    monthly = monthly.sort_values("date")

    # 2) Identify columns
    date_col = "date"
    bench_col = monthly.columns[1]      # iShares / benchmark column (we won’t use it now)
    stock_cols = list(monthly.columns[2:])

    # 3) Ensure numeric for stocks
    monthly[stock_cols] = monthly[stock_cols].apply(pd.to_numeric, errors="coerce")

    # 4) Compute monthly returns (pct_change) for each stock
    rets_wide = monthly[[date_col] + stock_cols].copy()
    rets_wide[stock_cols] = rets_wide[stock_cols].pct_change()

    # 5) Save wide (optional but handy)
    rets_wide.to_csv(OUT / "stock_returns_wide.csv", index=False)

    # 6) Long format (date, NR, ret_1m)
    rets_long = rets_wide.melt(
        id_vars=date_col, var_name="NR", value_name="ret_1m"
    ).dropna(subset=["ret_1m"])

    # 7) Basic sanity filters (optional)
    # Remove absurd returns if any data glitches (e.g., > +/- 200%)
    rets_long = rets_long[(rets_long["ret_1m"] > -2.0) & (rets_long["ret_1m"] < 2.0)]

    # 8) Save long
    out_long = OUT / "stock_returns_long.csv"
    rets_long.to_csv(out_long, index=False)

    # 9) Quick summary
    print("✅ Built monthly returns")
    print("  →", OUT / "stock_returns_wide.csv")
    print("  →", OUT / "stock_returns_long.csv")
    print("Rows (long):", len(rets_long))
    print("Dates:", rets_long["date"].min(), "→", rets_long["date"].max())
    print("Sample:", rets_long.head(5).to_string(index=False))


if __name__ == "__main__":
    main()
