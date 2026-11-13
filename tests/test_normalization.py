
import sys
import unittest
from pathlib import Path
from datetime import date
from decimal import Decimal

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = PROJECT_ROOT / "src" / "ledgerflow"

sys.path.insert(0, str(SOURCE_DIR))

from normalization import (
    normalize_transaction_id,
    normalize_category,
    parse_amount,
    parse_transaction_date,
)


class TestNormalization(unittest.TestCase):

    def test_transaction_id_is_trimmed_and_uppercase(self):
        result = normalize_transaction_id("  txn-001  ")
        self.assertEqual(result, "TXN-001")

    def test_category_is_trimmed_and_case_normalized(self):
        result = normalize_category("  Hardware  ")
        self.assertEqual(result, "hardware")

    def test_amount_parses_currency_symbols_and_commas(self):
        result = parse_amount("$1,250.50")
        self.assertEqual(result, Decimal("1250.50"))

    def test_date_parses_us_format(self):
        result = parse_transaction_date("02/04/2024")
        self.assertEqual(result, date(2024, 2, 4))

    def test_date_parses_iso_format(self):
        result = parse_transaction_date("2024-02-04")
        self.assertEqual(result, date(2024, 2, 4))


if __name__ == "__main__":
    unittest.main()
