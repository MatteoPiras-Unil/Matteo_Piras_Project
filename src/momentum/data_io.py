# Load and return ready-to-use Dataframes

from pathlib import Path
import pandas as pd

RAW = Path("data/raw")

def load_monthly_data() -> pd.DataFrame:
    """Reads Monthly_Data.csv (semicolon-delimited), parses date, returns wide DataFrame."""
    path = RAW / "Monthly_Data.csv"
    df = pd.read_csv(path, sep=";")
    date_col = df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    return df.rename(columns={date_col: "date"})

def load_basic_data() -> pd.DataFrame:
    """Reads Basic_Data.csv (semicolon-delimited)."""
    path = RAW / "Basic_Data.csv"
    return pd.read_csv(path, sep=";")
