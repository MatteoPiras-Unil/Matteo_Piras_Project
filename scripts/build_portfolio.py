# scripts/build_portfolio.py
"""
Build momentum portfolios (Top 10/20/30/40/50) for a chosen lookback L in {1,3,6,12}.
Outputs:
- data/processed/portfolio_returns_top{N}_{L}m.csv
- results/portfolio_top{N}_{L}m.png                (individual cumulative charts)
- results/portfolios_vs_benchmark_{L}m.png         (all strategies + benchmark)
- results/performance_summary_{L}m.csv             (metrics table incl. p-HAC)
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

# make src importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from momentum.data_io import load_monthly_data
from momentum.metrics  import cum_index, metrics_table, align_common_start


DATA = Path("data/processed")
RES  = Path("results")
DATA.mkdir(parents=True, exist_ok=True)
RES.mkdir(parents=True, exist_ok=True)

PORT_SIZES = [10, 20, 30, 40, 50]


# ------------------------------
# I/O
# ------------------------------
def load_inputs(lookback: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """
    Load:
      - momentum_long_{L}m.csv (or momentum_long.csv if L=6 and specific file not present)
      - stock_returns_long.csv (long format, 1m returns)
      - benchmark monthly returns from raw levels (iShares column)
    """
    # momentum (universe already filtered to >10bn in your earlier pipeline)
    if lookback == 6:
        # prefer explicit _6m file if present, else fallback to legacy name
        cand = DATA / "momentum_long_6m.csv"
        mom_path = cand if cand.exists() else (DATA / "momentum_long.csv")
    else:
        mom_path = DATA / f"momentum_long_{lookback}m.csv"

    mom = pd.read_csv(mom_path)
    mom["date"] = pd.to_datetime(mom["date"], errors="coerce")
    mom["NR"]   = mom["NR"].astype(str)

    # returns
    rets_long = pd.read_csv(DATA / "stock_returns_long.csv")
    rets_long["date"]   = pd.to_datetime(rets_long["date"], errors="coerce")
    rets_long["NR"]     = rets_long["NR"].astype(str)
    rets_long["ret_1m"] = pd.to_numeric(rets_long["ret_1m"], errors="coerce")

    rets_wide = (
        rets_long.pivot(index="date", columns="NR", values="ret_1m")
                 .sort_index()
    )
    rets_wide.columns = rets_wide.columns.astype(str)

    # restrict to momentum universe (just in case)
    universe  = set(mom["NR"].astype(str).unique().tolist())
    keep_cols = [c for c in rets_wide.columns if c in universe]
    rets_wide = rets_wide.reindex(columns=keep_cols)

    # benchmark from raw levels (2nd column is iShares levels)
    levels   = load_monthly_data().copy().sort_values("date")
    date_col = "date"
    bench_col = levels.columns[1]
    levels[date_col] = pd.to_datetime(levels[date_col], errors="coerce")
    levels[bench_col] = (
        levels[bench_col]
        .astype(str)
        .str.replace(r"[^\d.\-eE]", "", regex=True)   # keep digits, -, e/E, dot
        .replace(r"^\s*$", np.nan, regex=True)
    )
    levels[bench_col] = pd.to_numeric(levels[bench_col], errors="coerce")

    bench = levels[[date_col, bench_col]].dropna(subset=[bench_col]).copy()
    bench["bench_ret"] = bench[bench_col].pct_change(fill_method=None)
    bench = bench.dropna(subset=["bench_ret"]).set_index(date_col)["bench_ret"]
    bench.name = "Benchmark"

    return mom, rets_wide, bench


# ------------------------------
# Portfolio construction
# ------------------------------
def build_portfolio_returns(
    mom: pd.DataFrame,
    rets_wide: pd.DataFrame,
    top_n: int,
    lookback: int
) -> pd.Series:
    """
    For each formation month t:
      - rank by mom_{L}m at t (descending)
      - hold those names in month t+1 and take equal-weight mean return
    Returns a pd.Series indexed by holding date (t+1).
    """
    mom = mom.copy()
    mom_col = f"mom_{lookback}m"

    out = []
    dates = sorted(mom["date"].dropna().unique())

    for t in range(len(dates) - 1):
        formation_date = pd.Timestamp(dates[t])
        holding_date   = pd.Timestamp(dates[t + 1])

        cross = mom[mom["date"] == formation_date].dropna(subset=[mom_col])
        if cross.empty:
            continue

        top    = cross.sort_values(mom_col, ascending=False).head(top_n)
        tickers = top["NR"].astype(str).tolist()

        if holding_date not in rets_wide.index:
            continue

        cols = [c for c in tickers if c in rets_wide.columns]
        if not cols:
            continue

        r = rets_wide.loc[holding_date, cols]
        if r.dropna().empty:
            continue

        out.append((holding_date, float(r.mean(skipna=True))))

    if not out:
        return pd.Series(dtype=float)

    idx = [d for d, _ in out]
    val = [v for _, v in out]
    return pd.Series(val, index=idx, name=f"top{top_n}_{lookback}m_ret")


# ------------------------------
# Plotting
# ------------------------------
def plot_single(cum: pd.Series, title: str, outfile: Path):
    plt.figure(figsize=(9, 5))
    plt.plot(cum.index, cum.values)
    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel("Cumulative value (start=1.0)")
    plt.tight_layout()
    plt.savefig(outfile, dpi=220)
    plt.close()


def plot_all(portfolios: dict[str, pd.Series], bench_cum: pd.Series, outfile: Path, lookback: int):
    plt.figure(figsize=(10, 6))
    # benchmark first
    plt.plot(bench_cum.index, bench_cum.values, label="Benchmark (iShares)")
    # then strategies
    for name, series in portfolios.items():
        plt.plot(series.index, series.values, label=name)
    plt.title(f"Momentum Portfolios vs Benchmark ({lookback}-month momentum)")
    plt.xlabel("Date")
    plt.ylabel("Cumulative value (start=1.0)")
    plt.legend()

    # event markers (optional)
    events = [
        ("2020-03-15", "COVID-19"),
        ("2025-03-01", "Tariff announcement"),
    ]
    _, ymax = plt.ylim()
    for date, label in events:
        d = pd.to_datetime(date)
        plt.axvline(x=d, color="gray", linestyle="--", linewidth=1.2, alpha=0.7)
        plt.text(d, ymax * 0.995, label, rotation=90, va="top", ha="right", fontsize=9, color="gray")

    plt.tight_layout()
    plt.savefig(outfile, dpi=220)
    plt.close()


# ------------------------------
# Args
# ------------------------------
def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lookback", type=int, default=6, choices=[1, 3, 6, 12],
                    help="Momentum lookback in months (default 6).")
    return ap.parse_args()


# ------------------------------
# Main
# ------------------------------
def main():
    args = parse_args()
    L = int(args.lookback)
    suffix = f"_{L}m"  # ALWAYS include suffix, even for 6m

    mom, rets_wide, bench = load_inputs(lookback=L)

    # portfolios monthly returns
    port_monthly: dict[int, pd.Series] = {}
    for n in PORT_SIZES:
        s = build_portfolio_returns(mom, rets_wide, n, L)
        port_monthly[n] = s
        # save monthly returns with suffix to avoid overwriting across horizons
        (DATA / f"portfolio_returns_top{n}{suffix}.csv").write_text(
            s.to_csv(header=True), encoding="utf-8"
        )

    # align all monthly-return series to common start (including benchmark)
    named = {f"Top {n}": port_monthly[n] for n in PORT_SIZES}
    named["Benchmark"] = bench
    aligned, bench_aligned, common_start = align_common_start(named, named["Benchmark"])
    print(f"Common start date: {common_start}")

    # cumulative indices for plots (rebased to 1 from common start)
    bench_cum = cum_index(bench_aligned, start=1.0)
    cum_dict  = {k: cum_index(v, start=1.0) for k, v in aligned.items() if k != "Benchmark"}

    # plots
    for n in PORT_SIZES:
        if not aligned[f"Top {n}"].empty:
            plot_single(
                cum_dict[f"Top {n}"],
                f"Momentum Portfolio Top {n} ({L}m)",
                RES / f"portfolio_top{n}{suffix}.png",
            )
    plot_all(cum_dict, bench_cum, RES / f"portfolios_vs_benchmark{suffix}.png", lookback=L)

    # metrics table (HAC p-values computed inside metrics_table)
    df_sum = metrics_table({**aligned, "Benchmark": bench_aligned})

    # OPTIONAL: freeze benchmark row in the CSV metrics table (plots unaffected)
    frozen_path = RES / "benchmark_metrics.csv"
    if frozen_path.exists():
        try:
            frozen = pd.read_csv(frozen_path, index_col=0)
            if "Benchmark" in frozen.index and "Benchmark" in df_sum.index:
                common_cols = [c for c in frozen.columns if c in df_sum.columns]
                df_sum.loc["Benchmark", common_cols] = frozen.loc["Benchmark", common_cols]
        except Exception as e:
            print(f"[warn] Could not apply frozen benchmark metrics: {e}")

    # save metrics summary with suffix
    out_csv = RES / f"performance_summary{suffix}.csv"
    df_sum.to_csv(out_csv, index=True)

    # console summary
    pd.set_option("display.float_format", lambda x: f"{x:0.4f}")
    print("\n=== Performance Metrics (aligned sample) ===")
    print(df_sum)
    print("\nSaved:")
    print(f"  - {out_csv}")
    print(f"  - results/portfolios_vs_benchmark{suffix}.png")
    for n in PORT_SIZES:
        print(f"  - results/portfolio_top{n}{suffix}.png")
    for n in PORT_SIZES:
        print(f"  - data/processed/portfolio_returns_top{n}{suffix}.csv")


if __name__ == "__main__":
    main()

