
"""Build monthly stock return features for large-cap stocks (MktCap > $10B).
Saves both wide and long formats to data/processed/.
"""

from pathlib import Path
import sys

# Ensure we can import from src/
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
try:
    from momentum.data_io import load_monthly_data, load_basic_data
except ImportError:
    # Fallback: try to load the module directly from the src folder by file path
    import importlib.util

    src_root = Path(__file__).resolve().parents[1] / "src"
    module_path = src_root / "momentum" / "data_io.py"

    if module_path.exists():
        spec = importlib.util.spec_from_file_location("momentum.data_io", str(module_path))
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)  # type: ignore
        load_monthly_data = module.load_monthly_data
        load_basic_data = module.load_basic_data
    else:
        # ensure src is on sys.path and re-raise the import error for visibility
        sys.path.insert(0, str(src_root))
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
    """Convert a Series of strings to floats, stripping out non-numeric characters."""
    return (
        s.astype(str)
         .str.replace(r"[^\d.\-eE]", "", regex=True)  # keep digits, dot, minus, exponent
         .replace({"": None})
         .astype(float)
    )


def main() -> None:
    # 1) Load data
    monthly = load_monthly_data().copy()
    monthly = monthly.sort_values("date")  # ensure sorted by date
    basic = load_basic_data().copy()

    # 2) Identify key columns
    date_col = "date"
    # bench_col (monthly.columns[1]) is not needed elsewhere, so we omit assigning it to avoid an unused-variable warning
    all_stock_cols = list(monthly.columns[2:]) 

    # 3) Find linking column (NR) and Market Cap column in basic data
    nr_col = "NR"
    mcap_col = " Company Market Capitalization "


    if nr_col is None or mcap_col is None:
        raise ValueError(
            f"Could not find linking or market cap column. "
            f"Found NR-like: {nr_col}, MktCap-like: {mcap_col}. "
            f"Available columns: {list(basic.columns)}"
        )

    # 4) Filter basic data for large-cap stocks (MktCap > $10B)
    basic[nr_col] = basic[nr_col].astype(str).str.strip()
    basic[mcap_col] = _to_float_series(basic[mcap_col])

    eligible_ids = set(basic.loc[basic[mcap_col] > 10_000_000_000, nr_col].tolist())

    # Filter monthly data columns to only include eligible large-cap stocks
    stock_cols = [c for c in all_stock_cols if str(c) in eligible_ids]

    if len(stock_cols) == 0:
        raise ValueError(
            "No overlap between eligible large-cap NR codes and Monthly_Data columns. "
            f"Eligible IDs (sample): {list(sorted(eligible_ids))[:10]}"
        )

    print(f"Keeping {len(stock_cols)} large-cap stocks (MktCap > 10B).")
    print(f"Dropped {len(all_stock_cols) - len(stock_cols)} smaller-cap/absent columns.")

    # 5) Convert stock columns to numeric (coerce errors to NaN)
    monthly[stock_cols] = monthly[stock_cols].apply(pd.to_numeric, errors="coerce")

    # 6) Compute monthly returns
    rets_wide = monthly[[date_col] + stock_cols].copy()
    rets_wide[stock_cols] = rets_wide[stock_cols].pct_change(fill_method=None) 

    # 7) Save wide
    out_wide = OUT / "stock_returns_wide.csv"
    rets_wide.to_csv(out_wide, index=False)

    # 8) Melt to long format and clean
    rets_long = rets_wide.melt(id_vars=date_col, var_name="NR", value_name="ret_1m")
    rets_long = rets_long.dropna(subset=["ret_1m"])
    rets_long = rets_long[(rets_long["ret_1m"] > -2.0) & (rets_long["ret_1m"] < 2.0)]

    out_long = OUT / "stock_returns_long.csv"
    rets_long.to_csv(out_long, index=False)

    # 9) Summary output
    print("Built monthly returns for large-caps")
    print("  →", out_wide)
    print("  →", out_long)
    print("Rows (long):", len(rets_long))
    print("Dates:", rets_long["date"].min(), "→", rets_long["date"].max())
    print("Sample:", rets_long.head(5).to_string(index=False))


if __name__ == "__main__":
    main()