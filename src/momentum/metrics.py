# src/momentum/metrics.py
from __future__ import annotations
from scipy import stats
import numpy as np
import pandas as pd

def cum_index(returns: pd.Series, start: float = 1.0) -> pd.Series:
    """Cumulative index that starts exactly at `start` on the first date."""
    r = returns.sort_index()
    cum = (1.0 + r.fillna(0)).cumprod()
    cum = cum.shift(1, fill_value=1.0)  # anchor first point to 1.0
    return cum * start


def cagr(r: pd.Series) -> float:
    r = r.dropna()
    if r.empty: return np.nan
    total = (1 + r).prod()
    yrs = len(r) / 12.0
    return total**(1/yrs) - 1 if yrs > 0 else np.nan

def ann_vol(r: pd.Series) -> float:
    r = r.dropna()
    return r.std(ddof=1) * np.sqrt(12) if len(r) > 1 else np.nan

def sharpe(r: pd.Series, rf: float = 0.0) -> float:
    vol = ann_vol(r); ret = cagr(r)
    return ret / vol if vol and vol > 0 else np.nan

def max_drawdown(r: pd.Series) -> float:
    idx = cum_index(r, 1.0)
    peak = idx.cummax()
    dd = idx/peak - 1.0
    return dd.min() if not dd.empty else np.nan

def sortino(r: pd.Series) -> float:
    r = r.dropna()
    if r.empty: return np.nan
    neg = r[r < 0]
    if len(neg) == 0: return np.inf
    dvol = neg.std(ddof=1) * np.sqrt(12)
    ret = cagr(r)
    return ret / dvol if dvol and dvol > 0 else np.nan

def align_common_start(series_dict: dict[str|int, pd.Series], bench: pd.Series):
    """Trim all monthly-return series to a common start date."""
    starts = [s.index.min() for s in series_dict.values() if not s.empty]
    if not bench.empty: starts.append(bench.index.min())
    common_start = max(starts)
    aligned = {k: v[v.index >= common_start] for k, v in series_dict.items()}
    bench_aligned = bench[bench.index >= common_start]
    return aligned, bench_aligned, common_start

def metrics_table(named_series: dict[str, pd.Series], bench_name: str = "Benchmark") -> pd.DataFrame:
    """
    Compute metrics and a p-value testing whether each portfolio's mean monthly
    return differs from the benchmark's mean (paired t-test on aligned months).

    Columns: Ann.Return (CAGR), Ann.Vol, Sharpe, Sortino, p-value (vs Benchmark)
    """
    if bench_name not in named_series:
        raise ValueError(f"'{bench_name}' not found in named_series")

    bench = named_series[bench_name].dropna().sort_index()

    rows = []
    for name, s in named_series.items():
        s = s.dropna().sort_index()
        # metrics (always on the portfolio series itself)
        ret = cagr(s)
        vol = ann_vol(s)
        sh  = sharpe(s)
        so  = sortino(s)

        if name == bench_name:
            p_fmt = "—"  # no p-value for the benchmark vs itself
        else:
            # align by date (paired test)
            p_aligned, b_aligned = s.align(bench, join="inner")
            # if too few overlapping observations, return NaN
            if len(p_aligned) < 3:
                p_fmt = "NaN"
            else:
                # paired t-test (equivalent to t-test on differences vs 0)
                t_stat, p_val = stats.ttest_rel(p_aligned, b_aligned, nan_policy="omit")
                if np.isnan(p_val):
                    p_fmt = "NaN"
                elif p_val < 0.001:
                    p_fmt = f"{p_val:.4f}***"
                elif p_val < 0.01:
                    p_fmt = f"{p_val:.4f}**"
                elif p_val < 0.05:
                    p_fmt = f"{p_val:.4f}*"
                else:
                    p_fmt = f"{p_val:.4f}"

        rows.append([name, ret, vol, sh, so, p_fmt])

    df = pd.DataFrame(
        rows,
        columns=[
            "Portfolio",
            "Ann.Return (CAGR)",
            "Ann.Vol",
            "Sharpe",
            "Sortino",
            "p-value",
        ],
    ).set_index("Portfolio")

    return df