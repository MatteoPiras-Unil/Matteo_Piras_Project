""" This script computes and plots the relative cumulative performance of top-N portfolios"""

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

DATA = Path("data/processed")
RES  = Path("results"); RES.mkdir(exist_ok=True, parents=True)

def cum_index(r: pd.Series, start=1.0) -> pd.Series:
    r = r.dropna().sort_index()
    cum = (1 + r).cumprod()
    return cum.shift(1, fill_value=1.0) * start  # start exactly at 1.0

def load_port(n):
    s = pd.read_csv(DATA / f"portfolio_returns_top{n}.csv")
    s.iloc[:,0] = pd.to_datetime(s.iloc[:,0])
    s = pd.Series(pd.to_numeric(s.iloc[:,1], errors="coerce").values, index=s.iloc[:,0], name=f"Top {n}")
    return s.dropna()

def load_bench():
    from momentum.data_io import load_monthly_data
    df = load_monthly_data().sort_values("date")
    date_col, bench_col = "date", df.columns[1]
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df[bench_col] = pd.to_numeric(
        df[bench_col].astype(str).str.replace(r"[^\d.\-eE]", "", regex=True), errors="coerce"
    )
    bench = df[[date_col, bench_col]].dropna()
    bench = bench.set_index(date_col)[bench_col].pct_change(fill_method=None).dropna()
    bench.name = "Benchmark"
    return bench

def main():
    bench = load_bench()
    portfolios = {n: load_port(n) for n in [10,20,30,40,50]}

    # align monthly returns, build cumulative & ratio
    for n, rp in portfolios.items():
        rb = bench
        rp, rb = rp.align(rb, join="inner")
        cum_p = cum_index(rp, 1.0)
        cum_b = cum_index(rb, 1.0)
        rel   = (cum_p / cum_b).rename(f"Top {n} / Bench")

        # save CSV and plot
        out_csv = DATA / f"relative_top{n}.csv"
        rel.to_csv(out_csv, header=True)

        plt.figure(figsize=(9,5))
        plt.plot(rel.index, rel.values)
        plt.axhline(1.0, ls="--", lw=1, alpha=0.6)
        plt.title(f"Relative Cumulative Performance: Top {n} vs Benchmark")
        plt.ylabel("Ratio ( >1 = outperformance )")
        plt.xlabel("Date")
        plt.tight_layout()
        plt.savefig(RES / f"relative_top{n}.png", dpi=220)
        plt.close()

    # Optional: one combined plot
    plt.figure(figsize=(10,6))
    for n in [10,20,30,40,50]:
        rel = pd.read_csv(DATA / f"relative_top{n}.csv", parse_dates=[0], index_col=0).iloc[:,0]
        plt.plot(rel.index, rel.values, label=f"Top {n}")
    plt.axhline(1.0, ls="--", lw=1, alpha=0.6)
    plt.title("Relative Cumulative (Portfolio / Benchmark)")
    plt.ylabel("Ratio")
    plt.xlabel("Date")
    plt.legend()
    plt.tight_layout()
    plt.savefig(RES / "relative_all.png", dpi=220)
    plt.close()

if __name__ == "__main__":
    main()
