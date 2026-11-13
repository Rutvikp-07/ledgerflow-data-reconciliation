
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = PROJECT_ROOT / "src" / "ledgerflow"

sys.path.insert(0, str(SOURCE_DIR))

from pipeline import run_quality_pipeline


class TestCompletePipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.result = run_quality_pipeline()

    def test_pipeline_loads_all_ledger_records(self):
        self.assertEqual(
            len(self.result["source_records"]), 1232
        )

    def test_pipeline_loads_all_bank_records(self):
        self.assertEqual(
            len(self.result["bank_records"]), 1180
        )

    def test_validation_accounts_for_every_record(self):
        validation = self.result["validation"]

        total = (
            len(validation["clean_records"])
            + len(validation["flagged_records"])
            + len(validation["rejected_records"])
        )

        self.assertEqual(total, 1232)

    def test_pipeline_generates_reconciliation_results(self):
        reconciliation = self.result["reconciliation"]

        self.assertGreater(reconciliation["total_results"], 0)

    def test_pipeline_generates_anomaly_report(self):
        anomalies = self.result["anomalies"]

        self.assertGreater(anomalies["total_anomalies"], 0)


if __name__ == "__main__":
    unittest.main()
