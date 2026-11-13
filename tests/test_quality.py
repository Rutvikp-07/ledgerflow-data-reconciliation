
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = PROJECT_ROOT / "src" / "ledgerflow"

sys.path.insert(0, str(SOURCE_DIR))

from quality import load_quality_config, validate_ledger_record


class TestDataQuality(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.config = load_quality_config()

    def valid_record(self):
        return {
            "txn_id": "TXN-TEST-001",
            "account_id": "ACC-TEST-001",
            "txn_date": "02/04/2024",
            "amount": "1250.50",
            "currency": "USD",
            "category": "Hardware",
            "merchant": "Test Merchant",
            "description": "Test transaction",
        }

    def test_valid_record_is_clean(self):
        result = validate_ledger_record(
            self.valid_record(), self.config
        )
        self.assertEqual(result["status"], "CLEAN")

    def test_invalid_amount_is_rejected(self):
        record = self.valid_record()
        record["amount"] = "invalid"

        result = validate_ledger_record(record, self.config)

        self.assertEqual(result["status"], "REJECTED")

    def test_invalid_date_is_rejected(self):
        record = self.valid_record()
        record["txn_date"] = "not-a-date"

        result = validate_ledger_record(record, self.config)

        self.assertEqual(result["status"], "REJECTED")

    def test_missing_category_is_flagged(self):
        record = self.valid_record()
        record["category"] = ""

        result = validate_ledger_record(record, self.config)

        self.assertEqual(result["status"], "FLAGGED")


if __name__ == "__main__":
    unittest.main()
