# scripts/summarize_results.py
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

RES = Path("results")
RES.mkdir(parents=True, exist_ok=True)

HORIZONS = [1, 3, 6, 12]
TOPNS = [10, 20, 30, 40, 50]

def _normalize_perf_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize various header variants to: Ann.Return, Ann.Vol, Sharpe (keep others if present)."""
    df = df.copy()

    # If "Portfolio" is a column, make it the index
    if "Portfolio" in df.columns:
        df["Portfolio"] = df["Portfolio"].astype(str)
        df = df.set_index("Portfolio")

    # Strip whitespace from col names
    df.columns = [c.strip() for c in df.columns]

    # Map exact headers (and a few common variants) to a canonical schema
    rename_map = {
        "Ann. Return (CAGR)": "Ann.Return",
        "Ann.Return (CAGR)": "Ann.Return",
        "Annualized Return (CAGR)": "Ann.Return",
        "Annualised Return (CAGR)": "Ann.Return",

        "Ann. Vol": "Ann.Vol",
        "Ann Vol": "Ann.Vol",
        "Ann.Volatility": "Ann.Vol",
        "Annualized Volatility": "Ann.Vol",
        "Annualised Volatility": "Ann.Vol",

        "Sharpe": "Sharpe",
        "Sortino": "Sortino",

        "p-HAC (vs BM)": "p_HAC",
    }
    df = df.rename(columns=rename_map)
    return df

def load_perf(L: int) -> pd.DataFrame:
    """
    Load summary for horizon L (1/3/6/12).
    Tries results/performance_summary{suffix}.csv then results/metrics_summary{suffix}.csv.
    Normalizes to columns: Ann.Return, Ann.Vol, Sharpe.
    Returns only Top 10/20/30/40/50 rows.
    """
    suffix = f"_{L}m" if L != 6 else ""
    perf_path = RES / f"performance_summary{suffix}.csv"
    metr_path = RES / f"metrics_summary{suffix}.csv"

    if perf_path.exists():
        df = pd.read_csv(perf_path)
        source = perf_path
    elif metr_path.exists():
        df = pd.read_csv(metr_path)
        source = metr_path
    else:
        raise FileNotFoundError(
            f"Missing both:\n  - {perf_path}\n  - {metr_path}\n"
            f"Run build_portfolio.py (or compute_metrics.py) for L={L} first."
        )

    df = _normalize_perf_columns(df)

    # Ensure required columns exist after normalization
    needed = {"Ann.Return", "Ann.Vol", "Sharpe"}
    missing = needed - set(df.columns)
    if missing:
        raise ValueError(
            f"{source} is missing {sorted(missing)} after normalization. "
            f"Found columns: {list(df.columns)}"
        )

    # Keep Top-N rows only (drop Benchmark etc.)
    wanted = [f"Top {n}" for n in TOPNS]
    present = [w for w in wanted if w in df.index]
    if not present:
        raise ValueError(f"No Top N rows found in {source}. Index sample: {list(df.index)[:8]}")

    # Return just the needed metrics (others like Sortino/p_HAC can stay unused here)
    return df.loc[present, ["Ann.Return", "Ann.Vol", "Sharpe"]]

def wide_metric(metric: str) -> pd.DataFrame:
    """
    Build a matrix with rows=TopN, cols=horizon (1/3/6/12) for given metric.
    metric ∈ {"Sharpe","Ann.Return","Ann.Vol"}
    """
    frames = []
    for L in HORIZONS:
        df = load_perf(L)
        s = df[metric].rename(L)
        s.index = [int(x.split()[1]) for x in s.index]  # "Top 10" -> 10
        frames.append(s)
    wide = pd.concat(frames, axis=1).loc[TOPNS]
    wide.columns = [f"{L}m" for L in HORIZONS]
    return wide

def lineplot_by_horizon(wide: pd.DataFrame, metric_name: str, outfile: Path):
    plt.figure(figsize=(9.5, 6))
    for col in wide.columns:
        plt.plot(wide.index, wide[col], marker="o", label=col)
    plt.xlabel("Top N (number of stocks)")
    plt.ylabel(f"{metric_name} Ratio")
    plt.title(f"{metric_name} Ratio Top-N — across momentum horizons")
    plt.legend(title="Horizon")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(outfile, dpi=220)
    plt.close()

def topn_sensitivity(L: int, metric: str, outfile: Path):
    """Bar plot of metric vs TopN for a single horizon L."""
    df = load_perf(L)
    s = df[metric].copy()
    s.index = [int(x.split()[1]) for x in s.index]
    s = s.loc[TOPNS]
    plt.figure(figsize=(8, 5))
    plt.bar(s.index, s.values)
    plt.xticks(s.index, [str(x) for x in s.index])
    plt.xlabel("Top N")
    plt.ylabel(metric)
    plt.title(f"{metric} Top-N (momentum {L}m)")
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(outfile, dpi=220)
    plt.close()

def bestN_table(metric: str) -> pd.DataFrame:
    """
    For each horizon, report the TopN that maximizes the metric.
    Saves to results/horizon_bestN_table.csv
    """
    rows = []
    for L in HORIZONS:
        df = load_perf(L)
        s = df[metric].copy()
        idx_top = s.idxmax()  # e.g. "Top 40"
        best_n = int(idx_top.split()[1])
        rows.append({"Horizon": f"{L}m", "Best TopN (Sharpe)": best_n, "Sharpe": s.max()})
    out = pd.DataFrame(rows).set_index("Horizon")
    out.to_csv(RES / "horizon_bestN_table.csv")
    return out

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--focus_lookback",
        type=int,
        default=6,
        choices=[1, 3, 6, 12],
        help="Which horizon to use for the Top-N sensitivity plot (default 6).",
    )
    return ap.parse_args()

def main():
    args = parse_args()
    focus = args.focus_lookback

    vol_wide = wide_metric("Ann.Vol")
    lineplot_by_horizon(vol_wide, "Annualized Volatility", RES / "vol_vs_topN_by_horizon.png")

    # 1) Sharpe vs Top-N across horizons
    sharpe_wide = wide_metric("Sharpe")
    lineplot_by_horizon(sharpe_wide, "Sharpe", RES / "sharpe_vs_topN_by_horizon.png")

    # 2) CAGR vs Top-N across horizons
    cagr_wide = wide_metric("Ann.Return")
    lineplot_by_horizon(cagr_wide, "Annualized Return (CAGR)", RES / "cagr_vs_topN_by_horizon.png")

    # 3) Top-N sensitivity for a chosen horizon (default 6m)
    topn_sensitivity(focus, "Sharpe", RES / f"topN_sensitivity_{focus}m.png")

    # 4) Which Top-N is best (by Sharpe) per horizon
    best_tbl = bestN_table("Sharpe")
    print("\n=== Best TopN per horizon (by Sharpe) ===")
    print(best_tbl)

    print("\nSaved:")
    print(" - results/sharpe_vs_topN_by_horizon.png")
    print(" - results/cagr_vs_topN_by_horizon.png")
    print(f" - results/topN_sensitivity_{focus}m.png")
    print(" - results/horizon_bestN_table.csv")

if __name__ == "__main__":
    main()

