
import csv
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path


def generate_data_summaries(processed_records, reconciliation):
    """Generate date, category and reconciliation status summaries."""

    project_root = Path(__file__).resolve().parents[2]
    output_dir = project_root / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    date_summary = defaultdict(
        lambda: {"transaction_count": 0, "total_amount": Decimal("0")}
    )

    category_summary = defaultdict(
        lambda: {"transaction_count": 0, "total_amount": Decimal("0")}
    )

    # Summary by transaction date and category.
    for record in processed_records:

        txn_date = record.get("txn_date") or "UNKNOWN_DATE"
        category = record.get("category") or "UNKNOWN_CATEGORY"

        try:
            amount = Decimal(str(record.get("amount")))
        except (InvalidOperation, TypeError):
            amount = Decimal("0")

        date_summary[txn_date]["transaction_count"] += 1
        date_summary[txn_date]["total_amount"] += amount

        category_summary[category]["transaction_count"] += 1
        category_summary[category]["total_amount"] += amount

    # Summary by reconciliation status.
    status_summary = reconciliation["summary"]

    date_path = output_dir / "summary_by_date.csv"
    category_path = output_dir / "summary_by_category.csv"
    status_path = output_dir / "summary_by_status.csv"

    def save_grouped_summary(path, summary):
        with path.open(
            "w", newline="", encoding="utf-8"
        ) as file:

            writer = csv.writer(file, lineterminator="\n")

            writer.writerow([
                "Group",
                "Transaction_Count",
                "Total_Amount"
            ])

            for group, values in sorted(summary.items()):
                writer.writerow([
                    group,
                    values["transaction_count"],
                    str(values["total_amount"])
                ])

    save_grouped_summary(date_path, date_summary)
    save_grouped_summary(category_path, category_summary)

    with status_path.open(
        "w", newline="", encoding="utf-8"
    ) as file:

        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(["Status", "Count"])

        for status, count in sorted(status_summary.items()):
            writer.writerow([status, count])

    return {
        "date_summary": date_path,
        "category_summary": category_path,
        "status_summary": status_path,
        "date_groups": len(date_summary),
        "category_groups": len(category_summary),
        "status_groups": len(status_summary)
    }
