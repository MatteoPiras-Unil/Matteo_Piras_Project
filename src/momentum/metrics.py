# src/momentum/metrics.py
from __future__ import annotations
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

def metrics_table(named_series: dict[str, pd.Series]) -> pd.DataFrame:
    rows = []
    for name, s in named_series.items():
        rows.append([
            name, cagr(s), ann_vol(s), sharpe(s), sortino(s), max_drawdown(s), len(s)
        ])
    df = pd.DataFrame(rows, columns=[
        "Portfolio","Ann.Return (CAGR)","Ann.Vol","Sharpe","Sortino","Max Drawdown","Months"
    ]).set_index("Portfolio")
    return df
