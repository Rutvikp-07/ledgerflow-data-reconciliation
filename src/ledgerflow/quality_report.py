import csv
import json
from pathlib import Path
from collections import Counter


def generate_quality_report(validation, duplicates):
    """Generate an explainable summary of ledger data quality."""

    clean = validation["clean_records"]
    flagged = validation["flagged_records"]
    rejected = validation["rejected_records"]

    warning_counts = Counter()
    error_counts = Counter()

    for item in flagged:
        warning_counts.update(item["warnings"])

    for item in rejected:
        error_counts.update(item["errors"])

    total = validation["total_records"]

    report = {
        "project": "LedgerFlow",
        "total_records": total,
        "validation": {
            "clean": len(clean),
            "flagged": len(flagged),
            "rejected": len(rejected)
        },
        "duplicates": {
            "exact_duplicate_groups": len(
                duplicates["exact_duplicates"]
            ),
            "exact_duplicate_rows_removed": (
                duplicates["exact_duplicate_rows_removed"]
            ),
            "conflicting_duplicate_groups": len(
                duplicates["conflicting_duplicates"]
            ),
            "conflicting_duplicate_rows": (
                duplicates["conflicting_duplicate_rows"]
            )
        },
        "warning_reasons": dict(sorted(warning_counts.items())),
        "rejection_reasons": dict(sorted(error_counts.items())),
        "validation_percentages": {
            "clean": round(len(clean) / total * 100, 2) if total else 0,
            "flagged": round(len(flagged) / total * 100, 2) if total else 0,
            "rejected": round(len(rejected) / total * 100, 2) if total else 0
        }
    }

    return report


def save_quality_report(report):
    """Save quality report in deterministic JSON and CSV formats."""

    project_root = Path(__file__).resolve().parents[2]
    output_dir = project_root / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "quality_report.json"
    csv_path = output_dir / "quality_report.csv"

    with json_path.open("w", encoding="utf-8", newline="\n") as file:
        json.dump(report, file, indent=4, sort_keys=True)
        file.write("\n")

    rows = []

    def flatten(data, prefix=""):
        for key, value in data.items():
            name = f"{prefix}.{key}" if prefix else key

            if isinstance(value, dict):
                flatten(value, name)
            else:
                rows.append({
                    "metric": name,
                    "value": value
                })

    flatten(report)

    with csv_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["metric", "value"],
            lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)

    return json_path, csv_path

