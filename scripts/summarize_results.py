"""Script to summarize and visualize portfolio performance results across momentum horizons and Top-N selections."""
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

    if "Portfolio" in df.columns:
        df["Portfolio"] = df["Portfolio"].astype(str)
        df = df.set_index("Portfolio")

    df.columns = [c.strip() for c in df.columns]

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
    return df.rename(columns=rename_map)


def load_perf(L: int) -> pd.DataFrame:
    """Load summary for horizon L (1/3/6/12) from results/, normalized to key metrics."""
    suffix = f"_{L}m"
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

    needed = {"Ann.Return", "Ann.Vol", "Sharpe"}
    missing = needed - set(df.columns)
    if missing:
        raise ValueError(
            f"{source} is missing {sorted(missing)} after normalization. "
            f"Found columns: {list(df.columns)}"
        )

    wanted = [f"Top {n}" for n in TOPNS]
    present = [w for w in wanted if w in df.index]
    if not present:
        raise ValueError(f"No Top N rows found in {source}. Index sample: {list(df.index)[:8]}")

    return df.loc[present, ["Ann.Return", "Ann.Vol", "Sharpe"]]


def wide_metric(metric: str) -> pd.DataFrame:
    """Build a matrix with rows=TopN, cols=horizon (1/3/6/12) for a given metric."""
    frames = []
    for L in HORIZONS:
        df = load_perf(L)
        s = df[metric].rename(L)
        s.index = [int(x.split()[1]) for x in s.index]
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
    plt.xticks([10, 20, 30, 40, 50])
    plt.tight_layout()
    plt.savefig(outfile, dpi=220)
    plt.close()


def bestN_table(metric: str) -> pd.DataFrame:
    """For each horizon, report the TopN that maximizes the metric."""
    rows = []
    for L in HORIZONS:
        df = load_perf(L)
        s = df[metric].copy()
        idx_top = s.idxmax()
        best_n = int(idx_top.split()[1])
        rows.append({"Horizon": f"{L}m", "Best TopN (Sharpe)": best_n, "Sharpe": s.max()})
    out = pd.DataFrame(rows).set_index("Horizon")
    out.to_csv(RES / "horizon_bestN_table.csv")
    return out


def main():
    vol_wide = wide_metric("Ann.Vol")
    lineplot_by_horizon(vol_wide, "Annualized Volatility", RES / "vol_vs_topN_by_horizon.png")

    sharpe_wide = wide_metric("Sharpe")
    lineplot_by_horizon(sharpe_wide, "Sharpe", RES / "sharpe_vs_topN_by_horizon.png")

    cagr_wide = wide_metric("Ann.Return")
    lineplot_by_horizon(cagr_wide, "Annualized Return (CAGR)", RES / "cagr_vs_topN_by_horizon.png")

    best_tbl = bestN_table("Sharpe")
    print("\n=== Best TopN per horizon (by Sharpe) ===")
    print(best_tbl)

    print("\nSaved:")
    print(" - results/sharpe_vs_topN_by_horizon.png")
    print(" - results/cagr_vs_topN_by_horizon.png")
    print(" - results/vol_vs_topN_by_horizon.png")
    print(" - results/horizon_bestN_table.csv")


if __name__ == "__main__":
    main()
