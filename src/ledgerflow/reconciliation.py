
from collections import defaultdict, Counter
from decimal import Decimal, InvalidOperation
from ingestion import load_ledger, load_bank
import csv
import os


# 1. Load source data
ledger = load_ledger("../../data/raw/company_ledger.csv")
bank = load_bank("../../data/raw/bank_statement.json")

print("\nSource Record Counts:")
print("Company Ledger:", len(ledger))
print("Bank Statement:", len(bank))


# 2. Create transaction indexes
ledger_index = defaultdict(list)
bank_index = defaultdict(list)

for record in ledger:
    txn_id = record["txn_id"].strip()

    if txn_id:
        ledger_index[txn_id].append(record)

for record in bank:
    ledger_ref = record["ledger_ref"].strip()

    if ledger_ref:
        bank_index[ledger_ref].append(record)


# 3. Identify duplicates
duplicate_ledger_ids = {
    key: records
    for key, records in ledger_index.items()
    if len(records) > 1
}

duplicate_bank_refs = {
    key: records
    for key, records in bank_index.items()
    if len(records) > 1
}


# 4. Amount conversion
def parse_amount(value):
    cleaned_value = value.replace("$", "").replace(",", "").strip()
    return Decimal(cleaned_value)


# 5. Define report structure
reconciliation_results = []


def add_result(
    ledger_record,
    bank_record,
    status,
    notes="",
    ledger_candidates=""
):

    reconciliation_results.append({
        "bank_ref": bank_record.get("bank_ref", "") if bank_record else "",
        "ledger_ref": (
            ledger_record.get("txn_id", "")
            if ledger_record else
            bank_record.get("ledger_ref", "") if bank_record else ""
        ),
        "ledger_amount": ledger_record.get("amount", "") if ledger_record else "",
        "bank_amount": bank_record.get("amount", "") if bank_record else "",
        "ledger_account": ledger_record.get("account_id", "") if ledger_record else "",
        "bank_account": bank_record.get("account", "") if bank_record else "",
        "ledger_date": ledger_record.get("txn_date", "") if ledger_record else "",
        "bank_date": bank_record.get("posted_date", "") if bank_record else "",
        "ledger_currency": ledger_record.get("currency", "") if ledger_record else "",
        "bank_currency": bank_record.get("currency", "") if bank_record else "",
        "ledger_candidates": ledger_candidates,
        "status": status,
        "notes": notes
    })


# 6. Reconcile bank records
for bank_record in bank:

    ledger_ref = bank_record["ledger_ref"].strip()

    # No ledger reference
    if not ledger_ref:

        if bank_record["memo"].strip().lower() == "bank-only item":
            status = "EXPLICIT_BANK_ONLY"
            notes = "Bank explicitly identifies this as a bank-only item."
        else:
            status = "UNLINKED_BANK_TRANSACTION"
            notes = "No ledger reference; secondary matching may be required."

        add_result(None, bank_record, status, notes)
        continue

    # Duplicate bank references
    if len(bank_index[ledger_ref]) > 1:

        add_result(
            None,
            bank_record,
            "NEEDS_INVESTIGATION",
            "Duplicate bank references."
        )
        continue

    # Reference does not exist in ledger
    if ledger_ref not in ledger_index:

        add_result(
            None,
            bank_record,
            "MISSING_IN_LEDGER",
            "Bank reference does not exist in company ledger."
        )
        continue

    # Duplicate ledger transaction IDs
    if len(ledger_index[ledger_ref]) > 1:

        candidates = ledger_index[ledger_ref]

        candidate_details = []

        for candidate in candidates:
            detail = (
                f"Amount: {candidate.get('amount', '')}, "
                f"Account: {candidate.get('account_id', '')}, "
                f"Date: {candidate.get('txn_date', '')}"
            )

            candidate_details.append(detail)

        add_result(
            None,
            bank_record,
            "NEEDS_INVESTIGATION",
            "Multiple ledger records have the same transaction ID.",
            " | ".join(candidate_details)
        )
        continue

    # Single ledger record
    ledger_record = ledger_index[ledger_ref][0]

    try:
        ledger_amount = parse_amount(ledger_record["amount"])
        bank_amount = parse_amount(bank_record["amount"])

    except (InvalidOperation, ValueError):
        status = "INVALID_AMOUNT"
        notes = "Unable to parse one or both transaction amounts."

    else:

        if ledger_amount != bank_amount:
            status = "AMOUNT_MISMATCH"
            notes = "Ledger amount differs from bank amount."

        elif ledger_record["account_id"].strip() != bank_record["account"].strip():
            status = "ACCOUNT_MISMATCH"
            notes = "Ledger account differs from bank account."

        elif ledger_record["currency"].strip() != bank_record["currency"].strip():
            status = "CURRENCY_MISMATCH"
            notes = "Ledger currency differs from bank currency."

        else:
            status = "MATCHED"
            notes = "Reference, amount, account and currency match."

    add_result(ledger_record, bank_record, status, notes)


# 7. Identify ledger transactions missing from bank
for txn_id, records in ledger_index.items():

    if txn_id not in bank_index:

        for ledger_record in records:

            if len(records) > 1:
                status = "NEEDS_INVESTIGATION"
                notes = "Duplicate ledger ID with no corresponding bank reference."

            else:
                status = "MISSING_IN_BANK"
                notes = "Ledger transaction has no corresponding bank reference."

            add_result(ledger_record, None, status, notes)


# 8. Generate status summary
status_counts = Counter(
    result["status"]
    for result in reconciliation_results
)

print("\nReconciliation Summary:")

for status, count in sorted(status_counts.items()):
    print(f"{status}: {count}")

print("\nTotal Reconciliation Results:", len(reconciliation_results))


# 9. Export reports
os.makedirs("../../outputs", exist_ok=True)


# Detailed report
if reconciliation_results:

    with open(
        "../../outputs/reconciliation_results.csv",
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        fieldnames = list(reconciliation_results[0].keys())

        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(reconciliation_results)


# Summary report
with open(
    "../../outputs/reconciliation_summary.csv",
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.writer(file)
    writer.writerow(["Status", "Count"])

    for status, count in sorted(status_counts.items()):
        writer.writerow([status, count])


print("\nReports Generated Successfully!")
print("outputs/reconciliation_results.csv")
print("outputs/reconciliation_summary.csv")
