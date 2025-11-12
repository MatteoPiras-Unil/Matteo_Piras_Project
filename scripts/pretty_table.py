"""Generate pretty PNG tables from the *performance* summary CSV files (keep Benchmark)."""

from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

RES = Path("results")
RES.mkdir(parents=True, exist_ok=True)

HORIZONS = [1, 3, 6, 12]
TOPNS = [10, 20, 30, 40, 50]

def _normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "Portfolio" in df.columns:
        df["Portfolio"] = df["Portfolio"].astype(str)
        df = df.set_index("Portfolio")
    df.columns = [c.strip() for c in df.columns]
    rename = {
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
    } #rename is for consistency
    return df.rename(columns=rename)

def _sig(p: float | None) -> str:
    if pd.isna(p):
        return ""
    if p < 0.01: return "***"
    if p < 0.05: return "**"
    if p < 0.10: return "*"
    return ""

def _find_summary_path(lookback: int) -> Path:
    """Find the appropriate performance summary CSV for the given lookback period."""
    suffix = f"_{lookback}m" if lookback != 6 else "_6m"
    candidates = [
        RES / f"performance_summary{suffix}.csv",
        RES / f"metrics_summary{suffix}.csv",
    ]
    # Special case: for 6m, also accept generic filenames
    if lookback == 6:
        candidates += [
            RES / "performance_summary.csv",
            RES / "metrics_summary.csv",
        ]
    for p in candidates:
        if p.exists():
            print(f"[pretty_table] Using {p.name} for {lookback}m")
            return p
    raise FileNotFoundError(
        "Missing summary CSV. Expected one of:\n  - "
        + "\n  - ".join(str(p) for p in candidates)
        + f"\nRun: python scripts/build_portfolio.py --lookback {lookback} (and/or compute_metrics.py)."
    )

def _load_summary_for_horizon(lookback: int) -> pd.DataFrame:
    path = _find_summary_path(lookback)
    df = pd.read_csv(path)
    return _normalize_cols(df)

def _format_for_plot(df: pd.DataFrame) -> pd.DataFrame:
    # Keep only Top-N and Benchmark
    keep_rows = [f"Top {n}" for n in TOPNS if f"Top {n}" in df.index]
    if "Benchmark" in df.index:
        keep_rows.append("Benchmark")

    cols_order = ["Ann.Return", "Ann.Vol", "Sharpe", "Sortino", "p_HAC"]
    cols = [c for c in cols_order if c in df.columns]
    df = df.loc[keep_rows, cols].copy()

    # p-HAC formatting with significance stars
    if "p_HAC" in df.columns:
        raw = df["p_HAC"]
        num = pd.to_numeric(raw, errors="coerce")
        formatted = []
        for p_raw, p_num in zip(raw, num):
            if pd.notna(p_num):
                formatted.append(f"{p_num:.4f}{_sig(p_num)}")
            else:
                # Missing p-value
                formatted.append("" if pd.isna(p_raw) else str(p_raw))
        df["p-HAC (vs BM)"] = formatted
        df = df.drop(columns=["p_HAC"])

    # Numeric formatting
    num_fmt = {
        "Ann.Return": "{:.4f}",
        "Ann.Vol": "{:.4f}",
        "Sharpe": "{:.4f}",
        "Sortino": "{:.4f}",
    }
    for c, f in num_fmt.items():
        if c in df.columns:
            df[c] = df[c].map(lambda x: f.format(x) if pd.notna(x) else "")

    df.index.name = "Portfolio"
    return df

def _render_table_png(df: pd.DataFrame, title: str, outfile: Path):
    fig, ax = plt.subplots(figsize=(7.8, 2.6 + 0.38 * len(df)))
    ax.axis("off")
    table = ax.table(
        cellText=df.values,
        colLabels=df.columns,
        rowLabels=df.index,
        loc="center",
        cellLoc="center",
        rowLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.02, 1.28)
    ax.set_title(title, pad=12)
    plt.tight_layout()
    plt.savefig(outfile, dpi=220, bbox_inches="tight")
    plt.close()

def build_one(lookback: int):
    df = _load_summary_for_horizon(lookback)
    df_fmt = _format_for_plot(df)
    out = RES / f"metrics_table_{lookback}m.png"
    _render_table_png(df_fmt, f"Performance Metrics — {lookback}m Momentum", out)
    print(f"✅ Saved {out}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lookback", type=int, choices=[1,3,6,12],
                    help="Generate only for this horizon")
    args = ap.parse_args()

    if args.lookback:
        build_one(args.lookback)
    else:
        for L in HORIZONS:
            build_one(L)

if __name__ == "__main__":
    main()
