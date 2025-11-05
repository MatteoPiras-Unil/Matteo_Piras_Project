"""Build momentum features (long format) from monthly price data."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

# make src/ importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from momentum.data_io import load_monthly_data

OUT = Path("data/processed")
OUT.mkdir(parents=True, exist_ok=True)

LOOKBACKS = [1, 3, 6, 12]  # months

def compute_momentum(levels: pd.DataFrame, lookback: int) -> pd.DataFrame:
    """
    Compute momentum for each security over a given lookback (in months).

    For each date t we use end-of-previous-month prices so the formula is:
      momentum(t) = P_{t-1} / P_{t-1-L} - 1
    (this follows the common MSCI-style definition).

    The function returns a long-format DataFrame with columns:
      - date: observation date
      - NR: security identifier
      - mom_{L}m: the L-month momentum value

    Non-numeric or missing prices become NaN and are dropped from the result.
    """
    df = levels.copy()
    df = df.sort_values("date")
    date_col = "date"
    bench_col = df.columns[1]        # iShares/benchmark (ignored)
    stock_cols = list(df.columns[2:])

    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    # clean numeric
    for c in stock_cols:
        df[c] = pd.to_numeric(
            df[c].astype(str).str.replace(r"[^\d.\-eE]", "", regex=True),
            errors="coerce"
        )

    # price-based momentum (no day t, uses t-1 and t-1-L)
    px = df[[date_col] + stock_cols].set_index(date_col).sort_index()
    mom = px.shift(1) / px.shift(1 + lookback) - 1.0

    mom = mom.reset_index().melt(id_vars="date", var_name="NR", value_name=f"mom_{lookback}m")
    mom = mom.dropna(subset=[f"mom_{lookback}m"])

    # If you filtered >10B in your earlier step, you can intersect here if desired.
    return mom

def main():
    levels = load_monthly_data().copy()
    levels = levels.sort_values("date")

    for L in LOOKBACKS:
        momL = compute_momentum(levels, L)
        out_csv = OUT / f"momentum_long_{L}m.csv"
        momL.to_csv(out_csv, index=False)
        print(f"✅ Saved {out_csv}  (rows={len(momL)})")

if __name__ == "__main__":
    main()
