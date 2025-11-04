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
from pathlib import Path

# Make src importable
# Make src importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from momentum.data_io import load_monthly_data  # for benchmark levels


DATA = Path("data/processed")
RES = Path("results")
DATA.mkdir(parents=True, exist_ok=True)
RES.mkdir(parents=True, exist_ok=True)

PORT_SIZES = [10, 20, 30, 40, 50]


def load_inputs():
    # Momentum (already >10B based on your build_momentum.py)
    mom = pd.read_csv(DATA / "momentum_long.csv")
    mom["date"] = pd.to_datetime(mom["date"], errors="coerce")

    # Returns (1m) for ALL stocks; intersect with momentum NR universe
    rets_long = pd.read_csv(DATA / "stock_returns_long.csv")
    rets_long["date"] = pd.to_datetime(rets_long["date"], errors="coerce")

    # Ensure returns are numeric (in case CSV saved them as strings)
    rets_long["ret_1m"] = pd.to_numeric(rets_long["ret_1m"], errors="coerce")
    rets_long["NR"] = rets_long["NR"].astype(str)

    # Pivot returns to wide for fast selection
    rets_wide = (
        rets_long.pivot(index="date", columns="NR", values="ret_1m")
        .sort_index()
    )

    # Universe from momentum file
    universe = sorted(mom["NR"].astype(str).unique().tolist())

    # Restrict returns to momentum universe (just in case)
    keep_cols = [c for c in rets_wide.columns.astype(str) if c in set(universe)]
    rets_wide = rets_wide.reindex(columns=keep_cols)

    # Benchmark from raw levels
    levels = load_monthly_data().copy().sort_values("date")
    date_col = "date"
    bench_col = levels.columns[1]  # iShares (second column)
    levels[date_col] = pd.to_datetime(levels[date_col], errors="coerce")

        # 🔧 Coerce benchmark to numeric (handles commas, %, weird symbols)
    levels[bench_col] = (
        levels[bench_col]
        .astype(str)
        .str.replace(r"[^\d.\-eE]", "", regex=True)  # keep digits, minus, e/E, and dots
        .replace(r"^\s*$", np.nan, regex=True)       # empty strings to NaN
    )

    # Some Excel dumps may leave garbage like 'EE.E-E' or '--'
    levels[bench_col] = pd.to_numeric(levels[bench_col], errors="coerce")

    bench = levels[[date_col, bench_col]].dropna(subset=[bench_col]).copy()
    bench["bench_ret"] = bench[bench_col].pct_change(fill_method=None)
    bench = bench.dropna(subset=["bench_ret"]).set_index(date_col)["bench_ret"]

    return mom, rets_wide, bench



def build_portfolio_returns(mom: pd.DataFrame, rets_wide: pd.DataFrame, top_n: int) -> pd.Series:
    """
    For each formation month t:
      - rank by mom_6m at t (descending)
      - hold those names in month t+1 and take equal-weight mean return
    Returns a pd.Series indexed by holding date (t+1): monthly portfolio returns.
    """
    mom = mom.copy()
    mom["NR"] = mom["NR"].astype(str)

    port_rets = []
    dates = sorted(mom["date"].dropna().unique())

    for t in range(len(dates) - 1):  # last date has no t+1 to realize returns
        formation_date = pd.Timestamp(dates[t])
        holding_date = pd.Timestamp(dates[t + 1])

        cross = mom[mom["date"] == formation_date].dropna(subset=["mom_6m"])
        if cross.empty:
            continue

        top = cross.sort_values("mom_6m", ascending=False).head(top_n)
        tickers = top["NR"].astype(str).tolist()

        # Get realized next-month returns for those tickers
        if holding_date not in rets_wide.index:
            continue
        r = rets_wide.loc[holding_date, tickers]
        if r.dropna().empty:
            continue

        port_rets.append((holding_date, float(r.mean(skipna=True))))

    if not port_rets:
        return pd.Series(dtype=float)

    index = [d for d, _ in port_rets]
    values = [v for _, v in port_rets]
    return pd.Series(values, index=index, name=f"top{top_n}_ret")


def cum_index(returns: pd.Series, start=1.0) -> pd.Series:
    """Convert monthly returns series to a cumulative index starting at `start`."""
    return (1.0 + returns.fillna(0)).cumprod() * start


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
    plt.tight_layout()
    plt.savefig(outfile, dpi=220)
    plt.close()


def main():
    mom, rets_wide, bench = load_inputs()

    # Build portfolio monthly returns for each N
    port_monthly = {}
    for n in PORT_SIZES:
        s = build_portfolio_returns(mom, rets_wide, n)
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

    # Make a combined plot
    cum_dict = {f"Top {n}": cum_index(port_monthly[n], start=1.0).reindex(bench_cum.index, method="nearest")
                for n in PORT_SIZES}
    plot_all(cum_dict, bench_cum, RES / "portfolios_vs_benchmark.png")

    # Print quick metrics table
    print("\n=== Performance summary (monthly → annualized) ===")
    rows = []
    for n in PORT_SIZES:
        m = annualized_metrics(port_monthly[n])
        rows.append([f"Top {n}", m["ann_return"], m["ann_vol"], m["sharpe"]])
    # Benchmark metrics
    bm = annualized_metrics(bench.rename("bench_ret"))
    rows.append(["Benchmark", bm["ann_return"], bm["ann_vol"], bm["sharpe"]])

    df_sum = pd.DataFrame(rows, columns=["Portfolio", "Ann.Return", "Ann.Vol", "Sharpe"]).set_index("Portfolio")
    pd.set_option("display.float_format", lambda x: f"{x:0.4f}")
    print(df_sum)
    # Also save summary
    df_sum.to_csv(RES / "performance_summary.csv")
    print("\nSaved:")
    print("  - results/portfolios_vs_benchmark.png")
    for n in PORT_SIZES:
        print(f"  - results/portfolio_top{n}.png")
    print("  - results/performance_summary.csv")
    for n in PORT_SIZES:
        print(f"  - data/processed/portfolio_returns_top{n}.csv")


if __name__ == "__main__":
    main()
