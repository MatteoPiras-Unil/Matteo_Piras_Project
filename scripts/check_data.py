import pandas as pd
from pathlib import Path

# Path to the data folder
RAW = Path("data/raw")

#Load Monthly_Data.csv
m_path = RAW / "Monthly_Data.csv"
md = pd.read_csv(m_path, sep=";")   # <--- important: sep=";" for European CSV
print("✅ Monthly_Data.csv loaded!")
print("Shape:", md.shape)
print("First 5 columns:", list(md.columns[:5]))
print(md.head(3), "\n")

# Try parsing first column as dates (should be dates)
date_col = md.columns[0]
try:
    md[date_col] = pd.to_datetime(md[date_col], errors="coerce")
    print(f"Date range for '{date_col}':", md[date_col].min(), "→", md[date_col].max())
except Exception as e:
    print(f"Could not parse '{date_col}' as dates:", e)

#Load Basic_Data.csv
b_path = RAW / "Basic_Data.csv"
bd = pd.read_csv(b_path, sep=";")
print("\n✅ Basic_Data.csv loaded!")
print("Shape:", bd.shape)
print("Columns:", list(bd.columns))
print(bd.head(3))
