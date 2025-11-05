# src/momentum/metrics.py
from __future__ import annotations
from scipy import stats
import numpy as np
import pandas as pd
import statsmodels.api as sm


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

def hac_t_pvalue(active: pd.Series, lags: int | None = None) -> tuple[float, float]:
    """
    Compute HAC t-statistic and p-value for mean of `active` series.
    """
    a = active.dropna().values
    if len(a) < 8:
        return np.nan, np.nan
    if lags is None:
        lags = max(1, int(round(len(a) ** 0.25)))
    X = np.ones((len(a), 1))                 # intercept-only regression (mean test)
    ols = sm.OLS(a, X).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return float(ols.tvalues[0]), float(ols.pvalues[0])


def align_common_start(series_dict: dict[str|int, pd.Series], bench: pd.Series):
    """Trim all monthly-return series to a common start date."""
    starts = [s.index.min() for s in series_dict.values() if not s.empty]
    if not bench.empty: starts.append(bench.index.min())
    common_start = max(starts)
    aligned = {k: v[v.index >= common_start] for k, v in series_dict.items()}
    bench_aligned = bench[bench.index >= common_start]
    return aligned, bench_aligned, common_start

def _p_stars(p: float) -> str:
    if np.isnan(p): return "NaN"
    if p < 0.01:    return f"{p:.4f}***"
    if p < 0.05:    return f"{p:.4f}**"
    if p < 0.10:    return f"{p:.4f}*"
    return f"{p:.4f}"

def metrics_table(named_series: dict[str, pd.Series], bench_name: str = "Benchmark") -> pd.DataFrame:
    """
    Compute metrics and HAC p-value for H0: mean(active) = 0,
    where active = portfolio - benchmark.
    Columns: Ann.Return (CAGR), Ann.Vol, Sharpe, Sortino, p-HAC (vs BM)
    """
    if bench_name not in named_series:
        raise ValueError(f"'{bench_name}' not found in named_series")

    bench = named_series[bench_name].dropna().sort_index()
    rows = []

    for name, s in named_series.items():
        s = s.dropna().sort_index()

        # Base metrics
        ret = cagr(s)
        vol = ann_vol(s)
        sh  = sharpe(s)
        so  = sortino(s)

        if name == bench_name:
            p_fmt = "—"
        else:
            # Align and test active returns with HAC
            p_aligned, b_aligned = s.align(bench, join="inner")
            active = (p_aligned - b_aligned)
            t_stat, p_val = hac_t_pvalue(active, lags=None)
            p_fmt = _p_stars(p_val)

        rows.append([name, ret, vol, sh, so, p_fmt])

    df = pd.DataFrame(
        rows,
        columns=[
            "Portfolio",
            "Ann.Return (CAGR)",
            "Ann.Vol",
            "Sharpe",
            "Sortino",
            "p-HAC (vs BM)",
        ],
    ).set_index("Portfolio")

    return df
