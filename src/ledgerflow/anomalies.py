
from collections import Counter
from decimal import Decimal
from pathlib import Path

from normalization import parse_amount, parse_transaction_date
from quality import load_quality_config


def detect_anomalies(records, config):
    """
    Detect explainable anomalies using configurable rules.

    Each anomaly includes the transaction ID, rule name,
    severity and explanation.
    """

    settings = config.get("anomaly_settings", {})
    reference_date = parse_transaction_date(
        settings.get("reference_date")
    )

    rules = settings.get("rules", [])

    anomalies = []

    for record in records:
        txn_id = str(record.get("txn_id", "")).strip()

        for rule in rules:
            check = rule.get("check")
            reason = None

            try:
                if check == "amount_above":
                    amount = parse_amount(record.get("amount"))
                    threshold = Decimal(str(rule["threshold"]))

                    if amount > threshold:
                        reason = (
                            f"Transaction amount {amount} exceeds "
                            f"threshold {threshold}."
                        )

                elif check == "date_after":
                    transaction_date = parse_transaction_date(
                        record.get("txn_date")
                    )

                    if transaction_date > reference_date:
                        reason = (
                            f"Transaction date {transaction_date} "
                            f"is after reference date {reference_date}."
                        )

                elif check == "weekend_date":
                    transaction_date = parse_transaction_date(
                        record.get("txn_date")
                    )

                    if transaction_date.weekday() >= 5:
                        reason = (
                            f"Transaction date {transaction_date} "
                            "falls on a weekend."
                        )

            except (ValueError, TypeError, KeyError):
                # Invalid records are handled by the quality module.
                continue

            if reason:
                anomalies.append({
                    "txn_id": txn_id,
                    "rule": rule.get("name", "unknown_rule"),
                    "severity": rule.get("severity", "WARNING"),
                    "description": rule.get("description", ""),
                    "reason": reason
                })

    summary = Counter(item["rule"] for item in anomalies)

    return {
        "total_anomalies": len(anomalies),
        "anomalies": anomalies,
        "summary": dict(sorted(summary.items()))
    }


def save_anomaly_report(result):
    """Save anomaly details as a deterministic CSV report."""

    import csv

    project_root = Path(__file__).resolve().parents[2]
    output_dir = project_root / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "anomaly_report.csv"

    fields = [
        "txn_id",
        "rule",
        "severity",
        "description",
        "reason"
    ]

    with output_path.open(
        "w", newline="", encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fields,
            lineterminator="\n"
        )

        writer.writeheader()
        writer.writerows(result["anomalies"])

    return output_path


if __name__ == "__main__":
    config = load_quality_config()

    print("Anomaly detection module loaded successfully.")
    print("Configured rules:", len(config["anomaly_settings"]["rules"]))
