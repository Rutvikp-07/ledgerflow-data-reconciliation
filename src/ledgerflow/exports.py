
import csv
import json
from decimal import Decimal
from datetime import date, datetime
from pathlib import Path


def make_json_safe(value):
    """Convert Python values into JSON-compatible values."""

    if isinstance(value, (date, datetime)):
        return value.isoformat()

    if isinstance(value, Decimal):
        return str(value)

    if isinstance(value, dict):
        return {
            key: make_json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [make_json_safe(item) for item in value]

    return value


def export_processed_ledger(validation, duplicates):
    """
    Export accepted, normalized ledger records.

    Exact duplicate copies are excluded.
    Conflicting duplicate records are preserved for investigation.
    Rejected records are exported separately.
    """

    project_root = Path(__file__).resolve().parents[2]

    output_dir = project_root / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Accepted records after exact duplicate removal.
    accepted = [
        item["record"]
        for item in duplicates["unique_records"]
    ]

    # Preserve conflicting duplicates for investigation.
    for group in duplicates["conflicting_duplicates"]:
        accepted.extend(
            item["record"] for item in group["records"]
        )

    # Convert normalized values into export-friendly strings.
    processed_records = []

    for record in accepted:
        processed_records.append({
            "txn_id": record.get("normalized_txn_id"),
            "account_id": record.get("account_id"),
            "txn_date": (
                record["normalized_date"].isoformat()
                if record.get("normalized_date") else None
            ),
            "amount": (
                str(record["normalized_amount"])
                if record.get("normalized_amount") is not None
                else None
            ),
            "currency": record.get("normalized_currency"),
            "category": record.get("normalized_category"),
            "merchant": record.get("merchant"),
            "description": record.get("description")
        })

    fields = [
        "txn_id",
        "account_id",
        "txn_date",
        "amount",
        "currency",
        "category",
        "merchant",
        "description"
    ]

    # Save processed CSV.
    csv_path = output_dir / "cleaned_ledger.csv"

    with csv_path.open(
        "w", newline="", encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fields,
            lineterminator="\n"
        )

        writer.writeheader()
        writer.writerows(processed_records)

    # Save processed JSON.
    json_path = output_dir / "cleaned_ledger.json"

    with json_path.open(
        "w", encoding="utf-8"
    ) as file:

        json.dump(
            make_json_safe(processed_records),
            file,
            indent=4,
            ensure_ascii=False
        )

        file.write("\n")

    # Export rejected records separately.
    rejected_records = [
        {
            "row_number": item["row_number"],
            "record": item["record"],
            "errors": item["errors"]
        }
        for item in validation["rejected_records"]
    ]

    rejected_path = output_dir / "rejected_ledger.json"

    with rejected_path.open(
        "w", encoding="utf-8"
    ) as file:

        json.dump(
            make_json_safe(rejected_records),
            file,
            indent=4,
            ensure_ascii=False
        )

        file.write("\n")

    return {
        "processed_csv": csv_path,
        "processed_json": json_path,
        "rejected_json": rejected_path,
        "processed_records": len(processed_records),
        "rejected_records": len(rejected_records)
    }

