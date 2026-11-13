
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = PROJECT_ROOT / "src" / "ledgerflow"

sys.path.insert(0, str(SOURCE_DIR))

from reconciliation import reconcile_transactions


class TestReconciliation(unittest.TestCase):

    def make_ledger(self, **overrides):
        record = {
            "txn_id": "TXN-001",
            "account_id": "ACC-001",
            "txn_date": "2024-02-04",
            "amount": "100.00",
            "currency": "USD",
            "merchant": "Test Merchant",
            "category": "hardware",
        }
        record.update(overrides)
        return record

    def make_bank(self, **overrides):
        record = {
            "bank_ref": "BNK-001",
            "ledger_ref": "TXN-001",
            "account": "ACC-001",
            "posted_date": "2024-02-05",
            "amount": "100.00",
            "currency": "USD",
            "memo": "Test Merchant",
        }
        record.update(overrides)
        return record

    def test_primary_matching_finds_matched_transaction(self):
        result = reconcile_transactions(
            [self.make_ledger()],
            [self.make_bank()]
        )

        self.assertEqual(result["summary"]["MATCHED"], 1)

    def test_amount_mismatch_is_detected(self):
        result = reconcile_transactions(
            [self.make_ledger()],
            [self.make_bank(amount="150.00")]
        )

        self.assertEqual(result["summary"]["AMOUNT_MISMATCH"], 1)

    def test_bank_transaction_missing_from_ledger(self):
        result = reconcile_transactions(
            [],
            [self.make_bank()]
        )

        self.assertEqual(result["summary"]["MISSING_IN_LEDGER"], 1)

    def test_ledger_transaction_missing_from_bank(self):
        result = reconcile_transactions(
            [self.make_ledger()],
            []
        )

        self.assertEqual(result["summary"]["MISSING_IN_BANK"], 1)

    def test_secondary_matching_works_without_ledger_reference(self):
        result = reconcile_transactions(
            [self.make_ledger()],
            [self.make_bank(ledger_ref="")]
        )

        self.assertEqual(result["summary"]["SECONDARY_MATCHED"], 1)

    def test_unlinked_bank_transaction_has_explanation(self):
        bank = self.make_bank(
            ledger_ref="",
            amount="999.00",
            memo="Unknown Merchant"
        )

        result = reconcile_transactions([], [bank])

        self.assertEqual(
            result["summary"]["UNLINKED_BANK_TRANSACTION"], 1
        )

        for item in result["results"]:
            if item["status"] != "MATCHED":
                self.assertTrue(item["notes"].strip())

    def test_every_non_matched_result_has_a_reason(self):
        ledger = self.make_ledger()
        bank = self.make_bank(amount="150.00")

        result = reconcile_transactions([ledger], [bank])

        non_matched = [
            item for item in result["results"]
            if item["status"] != "MATCHED"
        ]

        self.assertTrue(non_matched)

        for item in non_matched:
            self.assertTrue(item["notes"].strip())


if __name__ == "__main__":
    unittest.main()
