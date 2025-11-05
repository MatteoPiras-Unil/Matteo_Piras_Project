# scripts/build_portfolio.py
"""
Build 5 momentum portfolios (Top 10/20/30/40/50 by 6m MSCI momentum),
rebalance monthly, equal-weight, 1-month holding. Save:
- data/processed/portfolio_returns_{N}.csv
- results/portfolio_top{N}.png  (5 individual charts)
- results/portfolios_vs_benchmark.png (all strategies + benchmark)
"""

from __future__ import annotations
import sys
import argparse
from pathlib import Path

# Make src importable
# Make src importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from momentum.data_io import load_monthly_data 
from momentum.metrics import cum_index, metrics_table, align_common_start



DATA = Path("data/processed")
RES = Path("results")
DATA.mkdir(parents=True, exist_ok=True)
RES.mkdir(parents=True, exist_ok=True)

PORT_SIZES = [10, 20, 30, 40, 50]


def load_inputs(lookback: int = 6):
    # pick momentum file by horizon
    mom_path = DATA / (f"momentum_long_{lookback}m.csv" if lookback != 6 else "momentum_long.csv")
    if not mom_path.exists():
        # fallback to the generic file if L=6 and you didn’t create the _6m file
        mom_path = DATA / "momentum_long.csv"

    mom = pd.read_csv(mom_path)
    mom["date"] = pd.to_datetime(mom["date"], errors="coerce")
    mom["NR"] = mom["NR"].astype(str)

    # Returns (1m) for ALL stocks; intersect with momentum NR universe
    rets_long = pd.read_csv(DATA / "stock_returns_long.csv")
    rets_long["date"] = pd.to_datetime(rets_long["date"], errors="coerce")
    rets_long["ret_1m"] = pd.to_numeric(rets_long["ret_1m"], errors="coerce")
    rets_long["NR"] = rets_long["NR"].astype(str)

    rets_wide = (
        rets_long.pivot(index="date", columns="NR", values="ret_1m")
        .sort_index()
    )
    rets_wide.columns = rets_wide.columns.astype(str)

    universe = sorted(mom["NR"].astype(str).unique().tolist())
    keep_cols = [c for c in rets_wide.columns.astype(str) if c in set(universe)]
    rets_wide = rets_wide.reindex(columns=keep_cols)

    # Benchmark from raw levels (your existing code)
    levels = load_monthly_data().copy().sort_values("date")
    date_col = "date"
    bench_col = levels.columns[1]
    levels[date_col] = pd.to_datetime(levels[date_col], errors="coerce")

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

    return mom, rets_wide, bench




def build_portfolio_returns(mom: pd.DataFrame, rets_wide: pd.DataFrame, top_n: int, lookback: int) -> pd.Series:
    """Build equal-weight momentum portfolio with dynamic lookback."""
    mom_col = f"mom_{lookback}m"

    port_rets = []
    dates = sorted(mom["date"].dropna().unique())

    for t in range(len(dates) - 1):
        formation_date = pd.Timestamp(dates[t])
        holding_date = pd.Timestamp(dates[t + 1])

        # dynamically select the right momentum column
        cross = mom[mom["date"] == formation_date].dropna(subset=[mom_col])
        if cross.empty:
            continue

        top = cross.sort_values(mom_col, ascending=False).head(top_n)
        tickers = top["NR"].astype(str).tolist()

        if holding_date not in rets_wide.index:
            continue
        cols = [c for c in tickers if c in rets_wide.columns]
        if not cols:
            continue
        r = rets_wide.loc[holding_date, cols]
        if r.dropna().empty:
            continue

        port_rets.append((holding_date, float(r.mean(skipna=True))))

    if not port_rets:
        return pd.Series(dtype=float)

    index = [d for d, _ in port_rets]
    values = [v for _, v in port_rets]
    return pd.Series(values, index=index, name=f"top{top_n}_{lookback}m_ret")



def cum_index(returns: pd.Series, start: float = 1.0) -> pd.Series:
    """Cumulative index that starts exactly at `start` on the first date."""
    r = returns.sort_index()
    cum = (1.0 + r.fillna(0)).cumprod()
    cum = cum.shift(1, fill_value=1.0)  # anchor first point to 1.0
    return cum * start


def annualized_metrics(returns: pd.Series) -> dict:
    """Compute annualized return/vol/sharpe from monthly returns (rf=0)."""
    r = returns.dropna()
    if r.empty:
        return {"ann_return": np.nan, "ann_vol": np.nan, "sharpe": np.nan}
    # Geometric annualized return
    cum = (1 + r).prod()
    yrs = len(r) / 12.0
    ann_return = cum ** (1 / yrs) - 1 if yrs > 0 else np.nan
    ann_vol = r.std(ddof=1) * np.sqrt(12) if len(r) > 1 else np.nan
    sharpe = ann_return / ann_vol if (ann_vol and ann_vol > 0) else np.nan
    return {"ann_return": ann_return, "ann_vol": ann_vol, "sharpe": sharpe}


def plot_single(cum: pd.Series, title: str, outfile: Path):
    plt.figure(figsize=(9, 5))
    plt.plot(cum.index, cum.values)
    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel("Cumulative value (start=1.0)")
    plt.tight_layout()
    plt.savefig(outfile, dpi=200)
    plt.close()


def plot_all(portfolios: dict[str, pd.Series], bench_cum: pd.Series, outfile: Path):
    plt.figure(figsize=(10, 6))
    # Benchmark first
    plt.plot(bench_cum.index, bench_cum.values, label="Benchmark (iShares)")
    # Then strategies
    for name, series in portfolios.items():
        plt.plot(series.index, series.values, label=name)
    plt.title("Momentum Portfolios vs Benchmark")
    plt.xlabel("Date")
    plt.ylabel("Cumulative value (start=1.0)")
    plt.legend()
    events = [
    ("2020-03-15", "COVID-19"),
    ("2025-03-01", "Trump Tariff announcement")
    ]

    ymin, ymax = plt.ylim()
    for date, label in events:
        d = pd.to_datetime(date)
        plt.axvline(x=d, color="gray", linestyle="--", linewidth=1.2, alpha=0.7)
        plt.text(d, ymax * 0.995, label, rotation=90, va="top", ha="right", fontsize=9, color="gray")   
    plt.tight_layout()
    plt.savefig(outfile, dpi=220)
    plt.close()

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lookback", type=int, default=6, choices=[1,3,6,12],
                    help="Momentum lookback in months (default 6).")
    return ap.parse_args()


def main():
    args = parse_args()
    lookback = args.lookback
    

    mom, rets_wide, bench = load_inputs(lookback=lookback)

    # Build portfolio monthly returns for each N
    port_monthly = {}
    for n in PORT_SIZES:
        s = build_portfolio_returns(mom, rets_wide, n, lookback)
        port_monthly[n] = s
        # Save returns
        out_csv = DATA / f"portfolio_returns_top{n}.csv"
        s.to_csv(out_csv, header=True)
        # Plot single cumulative
        cum_s = cum_index(s, start=1.0)
        plot_single(cum_s, f"Momentum Portfolio Top {n}", RES / f"portfolio_top{n}.png")

    # Align everything with benchmark
    # Compute benchmark cumulative index from returns
    bench_cum = cum_index(bench, start=1.0)

        # ----- Align series to the same start date and rebase -----

    # 1) Compute monthly benchmark returns (already done above in load_inputs)
    # bench: pd.Series of monthly returns indexed by date

    # 2) Find a COMMON start date = max of each series' first valid date
    series_list = [s for s in port_monthly.values() if not s.empty]
    starts = [s.index.min() for s in series_list if not s.empty]
    if not bench.empty:
        starts.append(bench.index.min())
    common_start = max(starts)  # ensure everyone has data from here on
    print("Common start date:", common_start)

    # 3) Trim all monthly-return series to >= common_start
    bench_aligned = bench[bench.index >= common_start]
    ports_aligned = {n: s[s.index >= common_start] for n, s in port_monthly.items()}

    # 4) Rebase from 1.0 using the trimmed returns
    bench_cum = cum_index(bench_aligned, start=1.0)
    cum_dict = {f"Top {n}": cum_index(ports_aligned[n], start=1.0) for n in PORT_SIZES}

    # 5) Combined plot
    plot_all(cum_dict, bench_cum, RES / f"portfolios_vs_benchmark_{lookback}m.png")

    # Print quick metrics table (do NOT save; compute_metrics.py is the source of truth)
    print("\n=== Performance summary (monthly → annualized) ===")
    rows = []
    for n in PORT_SIZES:
        m = annualized_metrics(port_monthly[n])
        rows.append([f"Top {n}", m["ann_return"], m["ann_vol"], m["sharpe"]])

    bm = annualized_metrics(bench.rename("bench_ret"))
    rows.append(["Benchmark", bm["ann_return"], bm["ann_vol"], bm["sharpe"]])

    df_sum = pd.DataFrame(rows, columns=["Portfolio", "Ann.Return", "Ann.Vol", "Sharpe"]).set_index("Portfolio")
    pd.set_option("display.float_format", lambda x: f"{x:0.4f}")
    print(df_sum)

    print("\nSaved:")
    print("  - results/portfolios_vs_benchmark.png")
    for n in PORT_SIZES:
        print(f"  - results/portfolio_top{n}.png")
    for n in PORT_SIZES:
        print(f"  - data/processed/portfolio_returns_top{n}.csv")

    # Build a dict of monthly returns for metrics
    named = {f"Top {n}": port_monthly[n] for n in PORT_SIZES}
    named["Benchmark"] = bench

    # Align samples, then compute table
    aligned, bench_aligned, _ = align_common_start(named, named["Benchmark"])
    aligned["Benchmark"] = bench_aligned
    df_sum = metrics_table(aligned)

    print("\n=== Performance Metrics (from build_portfolio quick check) ===")
    pd.set_option("display.float_format", lambda x: f"{x:0.4f}")
    print(df_sum)
    #df_sum.to_csv(RES / "performance_summary.csv")



if __name__ == "__main__":
    main()
