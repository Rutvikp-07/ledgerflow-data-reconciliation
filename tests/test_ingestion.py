
import sys
import unittest
import tempfile
import json
import csv

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = PROJECT_ROOT / "src" / "ledgerflow"

sys.path.insert(0, str(SOURCE_DIR))

from ingestion import load_ledger_with_issues, load_ledger, load_bank


class TestIngestion(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_csv(self, filename, content):
        path = self.temp_path / filename
        path.write_text(content, encoding="utf-8")
        return path

    def test_valid_csv_loads_records(self):
        path = self.create_csv(
            "ledger.csv",
            "txn_id,amount,currency\n"
            "TXN-001,100,USD\n"
            "TXN-002,200,USD\n"
        )

        records, malformed = load_ledger_with_issues(path)

        self.assertEqual(len(records), 2)
        self.assertEqual(len(malformed), 0)

    def test_extra_columns_are_detected(self):
        path = self.create_csv(
            "extra.csv",
            "txn_id,amount\n"
            "TXN-001,100,USD\n"
        )

        records, malformed = load_ledger_with_issues(path)

        self.assertEqual(len(records), 1)
        self.assertIn("EXTRA_COLUMNS", malformed[0]["issues"])

    def test_missing_columns_are_detected_and_padded(self):
        path = self.create_csv(
            "missing.csv",
            "txn_id,amount,currency\n"
            "TXN-001,100\n"
        )

        records, malformed = load_ledger_with_issues(path)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["currency"], "")
        self.assertIn("MISSING_COLUMNS", malformed[0]["issues"])

    def test_empty_csv_raises_value_error(self):
        path = self.create_csv("empty.csv", "")

        with self.assertRaises(ValueError):
            load_ledger_with_issues(path)

    def test_duplicate_headers_raise_value_error(self):
        path = self.create_csv(
            "duplicate.csv",
            "txn_id,amount,amount\n"
            "TXN-001,100,200\n"
        )

        with self.assertRaises(ValueError):
            load_ledger_with_issues(path)

    def test_bank_json_loads_records(self):
        path = self.temp_path / "bank.json"

        data = {
            "records": [
                {"bank_ref": "BNK-001", "amount": "100"},
                {"bank_ref": "BNK-002", "amount": "200"},
            ]
        }

        path.write_text(json.dumps(data), encoding="utf-8")

        records = load_bank(path)

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["bank_ref"], "BNK-001")

    def test_load_ledger_compatibility_function(self):
        path = self.create_csv(
            "compatibility.csv",
            "txn_id,amount\n"
            "TXN-001,100\n"
        )

        records = load_ledger(path)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["txn_id"], "TXN-001")


if __name__ == "__main__":
    unittest.main()
