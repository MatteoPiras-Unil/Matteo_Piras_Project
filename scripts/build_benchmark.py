"""Build benchmark return series and compute frozen metrics."""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

"""Add src/ to sys.path for local imports."""
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from momentum.data_io import load_monthly_data
from momentum.metrics import cagr, ann_vol, sharpe, sortino

DATA = Path("data/processed")
RES  = Path("results")
DATA.mkdir(parents=True, exist_ok=True)
RES.mkdir(parents=True, exist_ok=True)

def main():
    """Build benchmark return series and compute frozen metrics."""
    # 1) load and clean benchmark level data
    levels = load_monthly_data().copy().sort_values("date")
    date_col = "date"
    bench_col = levels.columns[1]  # iShares / benchmark column

    levels[date_col] = pd.to_datetime(levels[date_col], errors="coerce")
    levels[bench_col] = (
        levels[bench_col].astype(str)
        .str.replace(r"[^\d.\-eE]", "", regex=True)
        .replace(r"^\s*$", np.nan, regex=True)
    )
    levels[bench_col] = pd.to_numeric(levels[bench_col], errors="coerce")

    bench = levels[[date_col, bench_col]].dropna(subset=[bench_col]).copy()
    bench["bench_ret"] = bench[bench_col].pct_change(fill_method=None)
    bench = bench.dropna(subset=["bench_ret"]).set_index(date_col)["bench_ret"]
    bench.name = "Benchmark"

    # 2) save the return series once.
    out_returns = DATA / "benchmark_returns.csv"
    bench.to_frame("bench_ret").to_csv(out_returns)
    print(f"Saved {out_returns}")

    # 3) compute and save frozen metrics.
    ret = cagr(bench)
    vol = ann_vol(bench)
    shp = sharpe(bench)
    sor = sortino(bench)

    frozen = pd.DataFrame(
        [[ret, vol, shp, sor, "—"]],
        index=["Benchmark"],
        columns=["Ann.Return (CAGR)", "Ann.Vol", "Sharpe", "Sortino", "p-HAC (vs BM)"],
    )
    out_metrics = RES / "benchmark_metrics.csv"
    frozen.to_csv(out_metrics)
    print(f"Saved {out_metrics}")

if __name__ == "__main__":
    main()
