
import json
from pathlib import Path

from normalization import (
    normalize_transaction_id,
    normalize_category,
    parse_amount,
    parse_transaction_date
)


def load_quality_config():
    """Load LedgerFlow quality rules."""

    project_root = Path(__file__).resolve().parents[2]
    config_path = project_root / "config" / "quality_rules.json"

    if not config_path.exists():
        raise FileNotFoundError(
            f"Quality configuration not found: {config_path}"
        )

    with config_path.open("r", encoding="utf-8") as file:
        config = json.load(file)

    if config.get("project") != "LedgerFlow":
        raise ValueError("Invalid project name in quality configuration")

    return config


def validate_ledger_record(record, config):
    """Validate one ledger record and return an explainable result."""

    errors = []
    warnings = []
    normalized = record.copy()

    for rule in config["validation_rules"]:
        field = rule["field"]
        value = record.get(field)
        check = rule["check"]

        if check == "not_null":
            if value is None or str(value).strip() == "":
                message = f"{field} is missing"
            else:
                continue

        elif check == "valid_decimal":
            try:
                parsed_amount = parse_amount(value)

                if parsed_amount is None:
                    message = f"{field} is missing"
                else:
                    normalized["normalized_amount"] = parsed_amount
                    continue

            except ValueError:
                message = f"{field} has an invalid amount"

        elif check == "valid_date":
            try:
                normalized["normalized_date"] = parse_transaction_date(value)
                continue
            except ValueError:
                message = f"{field} has an invalid date"

        elif check == "supported_currency":
            if str(value).strip().upper() != config["currency"]:
                message = f"{field} must be {config['currency']}"
            else:
                normalized["normalized_currency"] = str(value).strip().upper()
                continue

        else:
            continue

        if rule["severity"] == "ERROR":
            errors.append(message)
        elif rule["severity"] == "WARNING":
            warnings.append(message)

    normalized["normalized_txn_id"] = normalize_transaction_id(
        record.get("txn_id")
    )

    normalized["normalized_category"] = normalize_category(
        record.get("category")
    )

    if errors:
        status = "REJECTED"
    elif warnings:
        status = "FLAGGED"
    else:
        status = "CLEAN"

    return {
        "record": normalized,
        "status": status,
        "errors": errors,
        "warnings": warnings
    }

def validate_ledger_records(records, config):
    """Validate all ledger records and separate them by quality status."""

    clean_records = []
    flagged_records = []
    rejected_records = []

    for row_number, record in enumerate(records, start=2):
        result = validate_ledger_record(record, config)

        result["row_number"] = row_number

        if result["status"] == "CLEAN":
            clean_records.append(result)

        elif result["status"] == "FLAGGED":
            flagged_records.append(result)

        elif result["status"] == "REJECTED":
            rejected_records.append(result)

    return {
        "total_records": len(records),
        "clean_records": clean_records,
        "flagged_records": flagged_records,
        "rejected_records": rejected_records
    }
