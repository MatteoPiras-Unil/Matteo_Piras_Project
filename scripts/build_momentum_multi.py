"""Script to compute momentum factors over multiple lookback periods."""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd

# make src/ importable (try normal import first, fall back to loading module by path)
src_dir = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(src_dir))
try:
    from momentum.data_io import load_monthly_data
except (ImportError, AttributeError):
    import importlib.util
    module_path = src_dir / "momentum" / "data_io.py"
    spec = importlib.util.spec_from_file_location("momentum.data_io", str(module_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    load_monthly_data = getattr(module, "load_monthly_data")

OUT = Path("data/processed")
OUT.mkdir(parents=True, exist_ok=True)

LOOKBACKS = [1, 3, 6, 12]  # months

def compute_momentum(levels: pd.DataFrame, lookback: int) -> pd.DataFrame:
    """
    Compute price-based momentum over a specified lookback period.
    Parameters
    ----------
    levels : pd.DataFrame
        DataFrame containing date, benchmark, and stock price levels.
    lookback : int
        Lookback period in months for momentum calculation.
    Returns
    -------
    pd.DataFrame
        DataFrame with columns: date, NR (stock identifier), mom_{lookback}m
    """
    df = levels.copy()
    df = df.sort_values("date")
    date_col = "date"
    # bench_col (benchmark column) is not required for the momentum calculation
    stock_cols = list(df.columns[2:])

    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    # Convert stock columns to numeric, coercing errors to NaN
    for c in stock_cols:
        df[c] = pd.to_numeric(
            df[c].astype(str).str.replace(r"[^\d.\-eE]", "", regex=True),
            errors="coerce"
        )

    # Calculate momentum: (Price_t-1 / Price_t-(1+lookback)) - 1
    px = df[[date_col] + stock_cols].set_index(date_col).sort_index()
    mom = px.shift(1) / px.shift(1 + lookback) - 1.0

    mom = mom.reset_index().melt(id_vars="date", var_name="NR", value_name=f"mom_{lookback}m")
    mom = mom.dropna(subset=[f"mom_{lookback}m"])

    return mom

def main():
    levels = load_monthly_data().copy()
    levels = levels.sort_values("date")

    for L in LOOKBACKS:
        momL = compute_momentum(levels, L)
        out_csv = OUT / f"momentum_long_{L}m.csv"
        momL.to_csv(out_csv, index=False)
        print(f"Saved {out_csv}  (rows={len(momL)})")

if __name__ == "__main__":
    main()
