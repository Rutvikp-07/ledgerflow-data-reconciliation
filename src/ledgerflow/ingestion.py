
import csv
import json


def load_ledger_with_issues(file_path):
    """
    Load ledger CSV records and identify malformed rows.

    Returns:
        records: All records, including malformed ones.
        malformed_rows: Details explaining malformed records.
    """

    records = []
    malformed_rows = []

    with open(file_path, "r", newline="", encoding="utf-8-sig") as file:
        reader = csv.reader(file)

        headers = next(reader, None)

        if not headers:
            raise ValueError("Ledger CSV is empty or has no header")

        if len(headers) != len(set(headers)):
            raise ValueError("Ledger CSV contains duplicate column names")

        for row_number, values in enumerate(reader, start=2):
            issues = []

            if len(values) > len(headers):
                issues.append("EXTRA_COLUMNS")

            if len(values) < len(headers):
                issues.append("MISSING_COLUMNS")

            # Preserve all expected columns.
            # Missing values are represented as empty strings.
            padded_values = values[:len(headers)]
            padded_values += [""] * (len(headers) - len(padded_values))

            record = dict(zip(headers, padded_values))
            records.append(record)

            if issues:
                malformed_rows.append({
                    "row_number": row_number,
                    "issues": issues,
                    "raw_values": values,
                    "record": record.copy()
                })

    return records, malformed_rows


def load_ledger(file_path):
    """Maintain compatibility with existing LedgerFlow modules."""
    records, _ = load_ledger_with_issues(file_path)
    return records


def load_bank(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data["records"]


if __name__ == "__main__":

    ledger, malformed = load_ledger_with_issues(
        "../../data/raw/company_ledger.csv"
    )

    bank = load_bank("../../data/raw/bank_statement.json")

    print("Company Ledger Records:", len(ledger))
    print("Malformed Ledger Rows:", len(malformed))
    print("Bank Statement Records:", len(bank))

    if malformed:
        print("First Malformed Row:", malformed[0])
