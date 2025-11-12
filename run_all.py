
"""
Master pipeline to rebuild all momentum portfolios, tables, and plots.
Runs the full workflow automatically:
    1. Build portfolios for all horizons
    2. Generate pretty PNG tables from metrics summaries
    3. Summarize results across horizons (Sharpe, Volatility, etc.)
"""

from __future__ import annotations
import subprocess

HORIZONS = [1, 3, 6, 12]

def run_step(desc: str, cmd: list[str]):
    print(f"\n=== {desc} ===")
    subprocess.run(cmd, check=True)

def main():
    # 1) Build portfolios and compute metrics
    for L in HORIZONS:
        run_step(f"STEP 1: Building portfolios for {L}m lookback", 
                 ["python", "scripts/build_portfolio.py", "--lookback", str(L)])

    # 2) Generate pretty tables for all horizons
    run_step("STEP 2: Generating metrics tables", 
             ["python", "scripts/pretty_table.py"])

    # 3) Summarize results across horizons
    run_step("STEP 3: Summarizing results", 
             ["python", "scripts/summarize_results.py"])

    print("\n All steps completed successfully.")

if __name__ == "__main__":
    main()

