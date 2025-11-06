#!/usr/bin/env python3
"""
Run all steps for the Matteo Piras Project:
1. Build portfolios for different lookback horizons.
2. Generate pretty PNG tables from summaries.
3. Summarize all results with plots and best TopN selections.
"""

import subprocess

# List of horizons (months)
horizons = [1, 3, 6, 12]

# 1️⃣ Build portfolios for each lookback horizon
for L in horizons:
    print(f"\n=== STEP 1: Building portfolios for {L}m lookback ===")
    subprocess.run(["python", "scripts/build_portfolio.py", "--lookback", str(L)], check=True)

# 2️⃣ Generate pretty PNG tables from summaries
print("\n=== STEP 2: Generating pretty tables ===")
for L in horizons:
    subprocess.run(["python", "scripts/pretty_table.py", "--lookback", str(L)], check=True)

# 3️⃣ Summarize all results (plots + best TopN)
print("\n=== STEP 3: Summarizing results ===")
subprocess.run(["python", "scripts/summarize_results.py"], check=True)

print("\n✅ All done! Check the 'results/' folder for outputs.")
