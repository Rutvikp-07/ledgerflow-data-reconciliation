
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SOURCE_DIR = PROJECT_ROOT / "src" / "ledgerflow"

sys.path.insert(0, str(SOURCE_DIR))

from pipeline import run_quality_pipeline


if __name__ == "__main__":
    run_quality_pipeline()
    print("\nLedgerFlow completed successfully.")
