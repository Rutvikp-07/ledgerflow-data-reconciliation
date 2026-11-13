
from normalization import (
    normalize_transaction_id,
    normalize_category,
    parse_amount,
    parse_transaction_date
)


def classify_ledger_duplicates(records):
    """Classify valid ledger records using normalized business values."""

    groups = {}

    for item in records:
        row_number = item["row_number"]
        record = item["record"]

        txn_id = normalize_transaction_id(record.get("txn_id"))

        if not txn_id:
            txn_id = f"__MISSING_ID_ROW_{row_number}"

        groups.setdefault(txn_id, []).append(item)

    unique_records = []
    exact_duplicates = []
    conflicting_duplicates = []
    removed_records = []

    def comparison_key(record):
        """Create a normalized key for business-data comparison."""

        amount = parse_amount(record.get("amount"))
        txn_date = parse_transaction_date(record.get("txn_date"))

        return (
            str(record.get("account_id", "")).strip().upper(),
            txn_date,
            amount,
            str(record.get("currency", "")).strip().upper(),
            normalize_category(record.get("category")),
            str(record.get("merchant", "")).strip().casefold(),
            str(record.get("description", "")).strip().casefold()
        )

    for txn_id, occurrences in groups.items():

        if len(occurrences) == 1:
            unique_records.append(occurrences[0])
            continue

        keys = [
            comparison_key(item["record"])
            for item in occurrences
        ]

        if all(key == keys[0] for key in keys[1:]):

            exact_duplicates.append({
                "txn_id": txn_id,
                "occurrences": len(occurrences),
                "kept_row": occurrences[0]["row_number"],
                "removed_count": len(occurrences) - 1
            })

            unique_records.append(occurrences[0])
            removed_records.extend(occurrences[1:])

        else:
            conflicting_duplicates.append({
                "txn_id": txn_id,
                "occurrences": len(occurrences),
                "records": occurrences,
                "reason": "Same transaction ID has different normalized business data"
            })

    return {
        "unique_records": unique_records,
        "exact_duplicates": exact_duplicates,
        "conflicting_duplicates": conflicting_duplicates,
        "removed_records": removed_records,
        "total_records": len(records),
        "exact_duplicate_rows_removed": len(removed_records),
        "conflicting_duplicate_rows": sum(
            item["occurrences"]
            for item in conflicting_duplicates
        )
    }
