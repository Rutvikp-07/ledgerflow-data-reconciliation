
from pathlib import Path

from ingestion import load_ledger_with_issues, load_bank
from quality import load_quality_config, validate_ledger_records
from duplicates import classify_ledger_duplicates
from quality_report import generate_quality_report, save_quality_report
from reconciliation import (
    reconcile_transactions,
    save_reconciliation_report
)
from anomalies import detect_anomalies, save_anomaly_report
from exports import export_processed_ledger
from summaries import generate_data_summaries


def run_quality_pipeline(ledger_path=None, bank_path=None):
    """
    Run the LedgerFlow pipeline.

    Optional:
        ledger_path: Path to an uploaded or existing ledger CSV.
        bank_path: Path to an uploaded or existing bank JSON file.

    If paths are not provided, default sample files are used.
    """

    project_root = Path(__file__).resolve().parents[2]

    if ledger_path is None:
        ledger_path = project_root / "data" / "raw" / "company_ledger.csv"

    if bank_path is None:
        bank_path = project_root / "data" / "raw" / "bank_statement.json"

    ledger_path = Path(ledger_path)
    bank_path = Path(bank_path)

    if not ledger_path.is_file():
        raise FileNotFoundError(f"Ledger file not found: {ledger_path}")

    if not bank_path.is_file():
        raise FileNotFoundError(f"Bank file not found: {bank_path}")

    # STEP 1: Load source data
    records, malformed_rows = load_ledger_with_issues(ledger_path)
    bank_records = load_bank(bank_path)

    # STEP 2: Load configuration and validate records
    config = load_quality_config()
    validation = validate_ledger_records(records, config)

    # STEP 3: Prepare accepted records
    accepted_records = [
        {
            "row_number": item["row_number"],
            "record": item["record"]
        }
        for item in (
            validation["clean_records"]
            + validation["flagged_records"]
        )
    ]

    # STEP 4: Classify duplicates
    duplicates = classify_ledger_duplicates(accepted_records)

    # STEP 5: Generate quality report
    report = generate_quality_report(validation, duplicates)
    report["malformed_rows"] = len(malformed_rows)

    report_paths = save_quality_report(report)

    # STEP 6: Detect anomalies
    anomaly_result = detect_anomalies(records, config)
    anomaly_path = save_anomaly_report(anomaly_result)

    # STEP 7: Prepare records for reconciliation
    reconciliation_ledger = [
        item["record"]
        for item in duplicates["unique_records"]
    ]

    for group in duplicates["conflicting_duplicates"]:
        reconciliation_ledger.extend(
            item["record"] for item in group["records"]
        )

    # STEP 8: Reconcile ledger against bank
    reconciliation = reconcile_transactions(
        reconciliation_ledger,
        bank_records
    )

    reconciliation_paths = save_reconciliation_report(
        reconciliation
    )

    # STEP 9: Export processed ledger records
    export_result = export_processed_ledger(
        validation,
        duplicates
    )

    # STEP 10: Generate data summaries
    processed_records = (
        [
            item["record"]
            for item in duplicates["unique_records"]
        ]
        + [
            item["record"]
            for group in duplicates["conflicting_duplicates"]
            for item in group["records"]
        ]
    )

    summaries = generate_data_summaries(
        processed_records,
        reconciliation
    )

    return {
        "source_records": records,
        "bank_records": bank_records,
        "malformed_rows": malformed_rows,
        "validation": validation,
        "duplicates": duplicates,
        "quality_report": report,
        "report_paths": report_paths,
        "anomalies": anomaly_result,
        "anomaly_path": anomaly_path,
        "reconciliation": reconciliation,
        "reconciliation_paths": reconciliation_paths,
        "exports": export_result,
        "summaries": summaries
    }


if __name__ == "__main__":
    result = run_quality_pipeline()

    print("\n========== LEDGERFLOW PIPELINE ==========")

    print("\nSOURCE DATA")
    print("Ledger records:", len(result["source_records"]))
    print("Bank records:", len(result["bank_records"]))
    print("Malformed rows:", len(result["malformed_rows"]))

    print("\nDATA QUALITY")
    print("Clean records:", len(result["validation"]["clean_records"]))
    print("Flagged records:", len(result["validation"]["flagged_records"]))
    print("Rejected records:", len(result["validation"]["rejected_records"]))

    print("\nDUPLICATE DETECTION")
    print(
        "Exact duplicate rows removed:",
        result["duplicates"]["exact_duplicate_rows_removed"]
    )
    print(
        "Conflicting duplicate groups:",
        len(result["duplicates"]["conflicting_duplicates"])
    )

    print("\nANOMALY DETECTION")
    print("Total anomalies:", result["anomalies"]["total_anomalies"])

    for rule, count in result["anomalies"]["summary"].items():
        print(f"{rule}: {count}")

    print("\nRECONCILIATION SUMMARY")
    print("Total results:", result["reconciliation"]["total_results"])

    for status, count in result["reconciliation"]["summary"].items():
        print(f"{status}: {count}")

    print("\nPROCESSED EXPORTS")
    print("Exported records:", result["exports"]["processed_records"])
    print("Rejected records:", result["exports"]["rejected_records"])

    for key, path in result["exports"].items():
        if key.endswith("_csv") or key.endswith("_json"):
            print(path)

    print("\nDATA SUMMARIES")
    print("Date groups:", result["summaries"]["date_groups"])
    print("Category groups:", result["summaries"]["category_groups"])
    print("Status groups:", result["summaries"]["status_groups"])

    for key, path in result["summaries"].items():
        if key.endswith("_summary"):
            print(path)

    print("\nREPORTS GENERATED")

    for path in result["report_paths"]:
        print(path)

    print(result["anomaly_path"])

    for path in result["reconciliation_paths"]:
        print(path)

    print("\nLedgerFlow pipeline completed successfully.")
