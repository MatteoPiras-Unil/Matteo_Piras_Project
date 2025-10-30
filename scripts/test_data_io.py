"""Make sure Python can see the "src" folder"""
import sys
from pathlib import Path

# Add the project root and src folder to Python's search path
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "src"))

# scripts/test_data_io.py
try:
    from momentum.data_io import load_monthly_data, load_basic_data
except ImportError:
    import importlib.util

    # Fallback: load the module directly from the src path if package import fails
    module_path = root / "src" / "momentum" / "data_io.py"
    if not module_path.exists():
        raise

    spec = importlib.util.spec_from_file_location("momentum.data_io", str(module_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    load_monthly_data = module.load_monthly_data
    load_basic_data = module.load_basic_data

def main():
    """ Load monthly data and run a quick test to ensure everything is working. """
    monthly = load_monthly_data()
    print("✅ Monthly data loaded!")
    print("Shape:", monthly.shape)
    print("Columns:", list(monthly.columns[:5]), "...")
    print(monthly.head(3), "\n")

    # Load basic data
    basic = load_basic_data()
    print("✅ Basic data loaded!")
    print("Shape:", basic.shape)
    print("Columns:", list(basic.columns))
    print(basic.head(3))

if __name__ == "__main__":
    main()
