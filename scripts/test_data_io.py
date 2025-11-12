""" Test script for data I/O functions in the momentum package. """
import sys
from pathlib import Path

# make src importable
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "src"))

# Import data I/O functions
try:
    from momentum.data_io import load_monthly_data, load_basic_data
except ImportError:
    import importlib.util

    
    module_path = root / "src" / "momentum" / "data_io.py"
    if not module_path.exists():
        raise

    spec = importlib.util.spec_from_file_location("momentum.data_io", str(module_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    load_monthly_data = module.load_monthly_data
    load_basic_data = module.load_basic_data

def main():
    """ Test loading of monthly and basic data. """
    monthly = load_monthly_data()
    print("Monthly data loaded!")
    print("Shape:", monthly.shape)
    print("Columns:", list(monthly.columns[:5]), "...")
    print(monthly.head(3), "\n")

    # Test basic data loading
    basic = load_basic_data()
    print("✅ Basic data loaded!")
    print("Shape:", basic.shape)
    print("Columns:", list(basic.columns))
    print(basic.head(3))

if __name__ == "__main__":
    main()
