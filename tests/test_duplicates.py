
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = PROJECT_ROOT / "src" / "ledgerflow"

sys.path.insert(0, str(SOURCE_DIR))

from duplicates import classify_ledger_duplicates


class TestDuplicateClassification(unittest.TestCase):

    def make_record(self, row_number, **overrides):
        record = {
            "txn_id": "TXN-001",
            "account_id": "ACC-001",
            "txn_date": "02/04/2024",
            "amount": "100.00",
            "currency": "USD",
            "category": "Hardware",
            "merchant": "Test Merchant",
            "description": "Test purchase",
        }

        record.update(overrides)

        return {
            "row_number": row_number,
            "record": record,
        }

    def test_records_without_duplicates_are_retained(self):
        records = [
            self.make_record(2, txn_id="TXN-001"),
            self.make_record(3, txn_id="TXN-002"),
        ]

        result = classify_ledger_duplicates(records)

        self.assertEqual(len(result["unique_records"]), 2)
        self.assertEqual(len(result["exact_duplicates"]), 0)
        self.assertEqual(len(result["conflicting_duplicates"]), 0)

    def test_exact_duplicates_keep_first_and_remove_extra(self):
        records = [
            self.make_record(2),
            self.make_record(3),
        ]

        result = classify_ledger_duplicates(records)

        self.assertEqual(len(result["unique_records"]), 1)
        self.assertEqual(len(result["exact_duplicates"]), 1)
        self.assertEqual(len(result["removed_records"]), 1)
        self.assertEqual(result["exact_duplicate_rows_removed"], 1)
        self.assertEqual(
            result["unique_records"][0]["row_number"], 2
        )

    def test_conflicting_duplicates_are_preserved(self):
        records = [
            self.make_record(2),
            self.make_record(3, amount="250.00"),
        ]

        result = classify_ledger_duplicates(records)

        self.assertEqual(len(result["unique_records"]), 0)
        self.assertEqual(len(result["conflicting_duplicates"]), 1)
        self.assertEqual(len(result["removed_records"]), 0)
        self.assertEqual(result["conflicting_duplicate_rows"], 2)

    def test_normalized_values_identify_exact_duplicates(self):
        records = [
            self.make_record(2, category="Hardware"),
            self.make_record(3, category="  HARDWARE  "),
        ]

        result = classify_ledger_duplicates(records)

        self.assertEqual(len(result["exact_duplicates"]), 1)
        self.assertEqual(len(result["removed_records"]), 1)


if __name__ == "__main__":
    unittest.main()
