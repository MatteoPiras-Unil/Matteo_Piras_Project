"""
Generate a 1-page PDF 'Dataset Summary Report' with:
- total stocks, total market cap
- largest/smallest company + share of total mcap
- avg/median market cap
- #stocks with MktCap > 10B (and share)
- date coverage from Monthly_Data
- #countries represented
- top 5 sectors by total market cap
- bar chart of top 10 companies by market cap

Output:
results/data_summary.pdf
results/top10_mcap.png

This is purely informative and not used in the main analysis."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional, List

# Make sure we can import from src/
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from momentum.data_io import load_basic_data, load_monthly_data

# ReportLab for PDF
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors


RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
CHART_PATH = RESULTS_DIR / "top10_mcap.png"
PDF_PATH = RESULTS_DIR / "data_summary.pdf"


def _find_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    """
    Find the first matching column in df from a list of candidate names (case-insensitive).
    Returns the original column name if found, else None.
    """
    norm2orig = {str(c).strip().lower(): c for c in df.columns}
    for cand in candidates:
        key = cand.strip().lower()
        if key in norm2orig:
            return norm2orig[key]
    return None


def _to_float_series(s: pd.Series) -> pd.Series:
    """Convert a Series to float, stripping non-numeric characters."""
    return (
        s.astype(str)
         .str.replace(r"[^\d.\-eE]", "", regex=True)  
         .replace({"": None})
         .astype(float)
    )


def _pick_label_col(basic: pd.DataFrame, name_col: Optional[str], symbol_col: Optional[str], nr_col: str) -> pd.Series:
    """ Pick the best available label column from name, symbol, or NR."""
    if name_col and name_col in basic.columns:
        labels = basic[name_col].astype(str).str.strip()
        if labels.notna().any():
            return labels
    if symbol_col and symbol_col in basic.columns:
        labels = basic[symbol_col].astype(str).str.strip()
        if labels.notna().any():
            return labels
    return basic[nr_col].astype(str)


def main() -> None:

    basic = load_basic_data().copy()
    monthly = load_monthly_data().copy()

    # --- Identify columns
    nr_col = _find_column(basic, ["NR", "Nr", "Id", "ID"])
    name_col = _find_column(basic, ["Company Common Name", "Common Name", "Name"])
    symbol_col = _find_column(basic, ["SYMBOL", "Symbol", "Ticker"])
    mcap_col = _find_column(
        basic,
        [
            "MktCap",
            "MarketCap",
            "Market Cap",
            "Company Market Capitalization",
            "Company Market Capitalization (Local)",
            "Market Capitalization",
            " Company Market Capitalization ",  # handles the exact case with spaces
        ],
    )
    sector_col = _find_column(basic, ["TRBC Economic Sector Name", "Sector", "GICS Sector"])
    country_col = _find_column(basic, ["Country ISO Code of Headquarters", "Country", "Country Code"])
    if nr_col is None or mcap_col is None:
        raise ValueError(
            f"Could not find linking or market cap column. "
            f"Found NR-like: {nr_col}, MktCap-like: {mcap_col}. "
            f"Available columns: {list(basic.columns)}"
        )

    # --- Preprocess columns
    basic[nr_col] = basic[nr_col].astype(str).str.strip()
    basic[mcap_col] = _to_float_series(basic[mcap_col])
    if sector_col:
        basic[sector_col] = basic[sector_col].astype(str).str.strip()
    if country_col:
        basic[country_col] = basic[country_col].astype(str).str.strip()

    # --- Compute statistics
    # Valid Market Cap entries
    valid = basic[basic[mcap_col].notna() & (basic[mcap_col] > 0)].copy()
    n_total = basic[nr_col].nunique()
    n_valid = valid[nr_col].nunique()
    total_mcap = float(valid[mcap_col].sum()) if n_valid > 0 else np.nan

    # Largest / smallest by mcap (among valid)
    largest = valid.loc[valid[mcap_col].idxmax()] if n_valid > 0 else None
    smallest = valid.loc[valid[mcap_col].idxmin()] if n_valid > 0 else None
    largest_share = (float(largest[mcap_col]) / total_mcap) if largest is not None and total_mcap > 0 else np.nan
    smallest_share = (float(smallest[mcap_col]) / total_mcap) if smallest is not None and total_mcap > 0 else np.nan

    avg_mcap = float(valid[mcap_col].mean()) if n_valid > 0 else np.nan
    med_mcap = float(valid[mcap_col].median()) if n_valid > 0 else np.nan

    over10b = valid[valid[mcap_col] > 10_000_000_000]
    n_over10b = int(over10b[nr_col].nunique())
    pct_over10b = (n_over10b / n_total) * 100 if n_total > 0 else 0.0

    # Date coverage from Monthly_Data
    monthly["date"] = pd.to_datetime(monthly["date"], errors="coerce")
    date_min = monthly["date"].min()
    date_max = monthly["date"].max()

    # Countries represented
    n_countries = basic[country_col].nunique() if country_col else None

    # Top 5 sectors by total market cap (using valid subset)
    if sector_col:
        sector_mcap = (
            valid.groupby(sector_col, dropna=False)[mcap_col]
            .sum()
            .sort_values(ascending=False)
            .head(5)
        )
        top5_sectors = list(sector_mcap.items())
    else:
        top5_sectors = []

        #-- Create bar chart of top 10 companies by market cap
    label_series = _pick_label_col(basic, name_col, symbol_col, nr_col)

    # Generate bar chart for top 10 by market cap
    labels_df = basic[[nr_col]].copy()
    labels_df["Label"] = label_series.astype(str).str.strip().values

    valid_labeled = valid.merge(labels_df, on=nr_col, how="left")

    top10 = valid_labeled.sort_values(mcap_col, ascending=False).head(10)
    if not top10.empty:
        plt.figure(figsize=(9, 5))
        plt.barh(top10["Label"].astype(str), top10[mcap_col].values)
        plt.gca().invert_yaxis()
        plt.xlabel("Market Cap, in billion")
        plt.title("Top 10 Companies by Market Cap")
        plt.tight_layout()
        plt.savefig(CHART_PATH, dpi=200)
        plt.close()


    # Build PDF
    doc = SimpleDocTemplate(str(PDF_PATH), pagesize=A4, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    title = Paragraph("<b>Dataset Summary Report</b>", styles["Title"])
    story.append(title)
    story.append(Spacer(1, 10))

    # Key figures table
    def fmt_money(x: float) -> str:
        return "-" if (x is None or np.isnan(x)) else f"${x:,.0f}"

    def fmt_pct(x: float) -> str:
        return "-" if (x is None or np.isnan(x)) else f"{x:.2f}%"

    largest_label = (largest[name_col] if (largest is not None and name_col) else
                     (largest[symbol_col] if (largest is not None and symbol_col) else
                      (largest[nr_col] if largest is not None else "-")))
    smallest_label = (smallest[name_col] if (smallest is not None and name_col) else
                      (smallest[symbol_col] if (smallest is not None and symbol_col) else
                       (smallest[nr_col] if smallest is not None else "-")))

    coverage = f"{date_min.date()} → {date_max.date()}" if pd.notna(date_min) and pd.notna(date_max) else "-"

    key_rows = [
        ["Total number of stocks (raw)", f"{n_total:,}"],
        ["Total with valid Market Cap", f"{n_valid:,}"],
        ["Total Market Capitalization", fmt_money(total_mcap)],
        ["Largest company (share of total)", f"{largest_label}  —  {fmt_money(float(largest[mcap_col]) if largest is not None else np.nan)}  ({fmt_pct(largest_share)})"],
        ["Smallest company (share of total)", f"{smallest_label}  —  {fmt_money(float(smallest[mcap_col]) if smallest is not None else np.nan)}  ({fmt_pct(smallest_share)})"],
        ["Average Market Cap", fmt_money(avg_mcap)],
        ["Median Market Cap", fmt_money(med_mcap)],
        ["# Stocks with MktCap > $10B", f"{n_over10b:,}  ({fmt_pct(pct_over10b)})"],
        ["Date coverage (monthly data)", coverage],
    ]
    if n_countries is not None:
        key_rows.append(["Countries represented", f"{n_countries:,}"])

    tbl = Table(key_rows, hAlign="LEFT", colWidths=[220, 300])
    tbl.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.whitesmoke, colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 12))

    # Top 5 sectors section
    if top5_sectors:
        story.append(Paragraph("<b>Top 5 Sectors by Total Market Cap</b>", styles["Heading3"]))
        sec_rows = [["Sector", "Total Market Cap"]]
        for name, val in top5_sectors:
            sec_rows.append([str(name), fmt_money(float(val))])
        sec_tbl = Table(sec_rows, hAlign="LEFT", colWidths=[280, 240])
        sec_tbl.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ]))
        story.append(sec_tbl)
        story.append(Spacer(1, 10))

    # Bar chart section
    if CHART_PATH.exists():
        story.append(Paragraph("<b>Top 10 Companies by Market Cap</b>", styles["Heading3"]))
        story.append(Spacer(1, 4))
        story.append(Image(str(CHART_PATH), width=480, height=300))
        story.append(Spacer(1, 6))

    doc.build(story)

    print("Summary report created:")
    print("  →", PDF_PATH)
    if CHART_PATH.exists():
        print("  →", CHART_PATH)


if __name__ == "__main__":
    main()
