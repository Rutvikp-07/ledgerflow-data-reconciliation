
from collections import defaultdict, Counter
from decimal import Decimal, InvalidOperation
from datetime import datetime
from pathlib import Path
import csv


def parse_amount(value):
    """Safely convert an amount into Decimal."""
    try:
        amount = Decimal(
            str(value).replace("$", "").replace(",", "").strip()
        )
        if not amount.is_finite():
            raise ValueError("Amount must be finite")
        return amount
    except (InvalidOperation, ValueError):
        raise ValueError(f"Invalid amount: {value}")


def parse_date(value):
    """Parse supported transaction dates."""
    if isinstance(value, datetime):
        return value.date()

    formats = ["%Y-%m-%d", "%m/%d/%Y", "%d %b %Y"]

    for date_format in formats:
        try:
            return datetime.strptime(
                str(value).strip(), date_format
            ).date()
        except ValueError:
            continue

    raise ValueError(f"Invalid date: {value}")


def reconcile_transactions(ledger_records, bank_records, tolerance_days=3):
    """
    Reconcile accepted ledger records against bank records.

    Primary matching:
        Uses the ledger transaction reference.

    Secondary matching:
        Uses account, amount, currency, merchant and posting date.

    Conflicting ledger IDs and ambiguous matches are
    preserved as investigation cases.
    """

    ledger_index = defaultdict(list)
    bank_index = defaultdict(list)
    results = []

    for record in ledger_records:
        txn_id = str(record.get("txn_id", "")).strip().upper()

        if txn_id:
            ledger_index[txn_id].append(record)

    for record in bank_records:
        ledger_ref = str(
            record.get("ledger_ref", "")
        ).strip().upper()

        if ledger_ref:
            bank_index[ledger_ref].append(record)

    processed_ledger_ids = set()
    unlinked_bank_records = []

    def add_result(ledger, bank, status, notes):
        results.append({
            "bank_ref": bank.get("bank_ref", "") if bank else "",
            "ledger_ref": (
                ledger.get("txn_id", "") if ledger
                else bank.get("ledger_ref", "") if bank else ""
            ),
            "ledger_amount": ledger.get("amount", "") if ledger else "",
            "bank_amount": bank.get("amount", "") if bank else "",
            "ledger_account": ledger.get("account_id", "") if ledger else "",
            "bank_account": bank.get("account", "") if bank else "",
            "ledger_date": ledger.get("txn_date", "") if ledger else "",
            "bank_date": bank.get("posted_date", "") if bank else "",
            "ledger_currency": ledger.get("currency", "") if ledger else "",
            "bank_currency": bank.get("currency", "") if bank else "",
            "status": status,
            "notes": notes
        })

    # --------------------------------------------------
    # STEP 1: PRIMARY MATCHING USING LEDGER REFERENCES
    # --------------------------------------------------

    for bank in bank_records:
        ledger_ref = str(
            bank.get("ledger_ref", "")
        ).strip().upper()

        if not ledger_ref:
            memo = str(
                bank.get("memo", "")
            ).strip().casefold()

            if memo == "bank-only item":
                add_result(
                    None,
                    bank,
                    "EXPLICIT_BANK_ONLY",
                    "Bank explicitly identifies this as a bank-only item."
                )
            else:
                unlinked_bank_records.append(bank)

            continue

        if len(bank_index[ledger_ref]) > 1:
            add_result(
                None,
                bank,
                "NEEDS_INVESTIGATION",
                "Multiple bank records have the same ledger reference."
            )
            continue

        if ledger_ref not in ledger_index:
            add_result(
                None,
                bank,
                "MISSING_IN_LEDGER",
                "Bank reference does not exist in the accepted ledger records."
            )
            continue

        candidates = ledger_index[ledger_ref]

        if len(candidates) > 1:
            add_result(
                None,
                bank,
                "NEEDS_INVESTIGATION",
                "Conflicting ledger records share this transaction ID."
            )
            continue

        ledger = candidates[0]
        processed_ledger_ids.add(ledger_ref)

        try:
            ledger_amount = parse_amount(ledger.get("amount"))
            bank_amount = parse_amount(bank.get("amount"))

            ledger_date = parse_date(ledger.get("txn_date"))
            bank_date = parse_date(bank.get("posted_date"))

        except ValueError as error:
            add_result(
                ledger,
                bank,
                "INVALID_DATA",
                str(error)
            )
            continue

        if ledger_amount != bank_amount:
            status = "AMOUNT_MISMATCH"
            notes = "Ledger amount differs from bank amount."

        elif str(ledger.get("account_id", "")).strip().upper() != str(
            bank.get("account", "")
        ).strip().upper():
            status = "ACCOUNT_MISMATCH"
            notes = "Ledger account differs from bank account."

        elif str(ledger.get("currency", "")).strip().upper() != str(
            bank.get("currency", "")
        ).strip().upper():
            status = "CURRENCY_MISMATCH"
            notes = "Ledger currency differs from bank currency."

        elif not 0 <= (bank_date - ledger_date).days <= tolerance_days:
            status = "DATE_MISMATCH"
            notes = (
                f"Bank posting date is outside the allowed "
                f"{tolerance_days}-day window."
            )

        else:
            status = "MATCHED"
            notes = (
                "Reference, amount, account, currency and date match."
            )

        add_result(ledger, bank, status, notes)

    # --------------------------------------------------
    # STEP 2: SECONDARY MATCHING FOR UNLINKED BANK ROWS
    # --------------------------------------------------

    for bank in unlinked_bank_records:
        candidates = []

        for txn_id, records in ledger_index.items():

            # Do not reuse an already processed ledger transaction.
            # Conflicting transaction IDs cannot be secondary matched.
            if txn_id in processed_ledger_ids or len(records) != 1:
                continue

            ledger = records[0]

            try:
                same_account = (
                    str(ledger.get("account_id", "")).strip().upper()
                    == str(bank.get("account", "")).strip().upper()
                )

                same_amount = (
                    parse_amount(ledger.get("amount"))
                    == parse_amount(bank.get("amount"))
                )

                same_currency = (
                    str(ledger.get("currency", "")).strip().upper()
                    == str(bank.get("currency", "")).strip().upper()
                )

                same_merchant = (
                    str(ledger.get("merchant", "")).strip().casefold()
                    == str(bank.get("memo", "")).strip().casefold()
                )

                date_difference = (
                    parse_date(bank.get("posted_date"))
                    - parse_date(ledger.get("txn_date"))
                ).days

                valid_date = (
                    0 <= date_difference <= tolerance_days
                )

            except (ValueError, TypeError):
                continue

            if (
                same_account
                and same_amount
                and same_currency
                and same_merchant
                and valid_date
            ):
                candidates.append(ledger)

        if len(candidates) == 1:
            ledger = candidates[0]

            txn_id = str(
                ledger.get("txn_id", "")
            ).strip().upper()

            processed_ledger_ids.add(txn_id)

            add_result(
                ledger,
                bank,
                "SECONDARY_MATCHED",
                (
                    "Matched using account, amount, currency, "
                    "merchant and posting date."
                )
            )

        elif len(candidates) > 1:
            add_result(
                None,
                bank,
                "NEEDS_INVESTIGATION",
                (
                    "Multiple ledger records satisfy the "
                    "secondary matching rules."
                )
            )

        else:
            add_result(
                None,
                bank,
                "UNLINKED_BANK_TRANSACTION",
                (
                    "No ledger record satisfies all "
                    "secondary matching rules."
                )
            )

    # --------------------------------------------------
    # STEP 3: FIND LEDGER RECORDS WITHOUT BANK RECORDS
    # --------------------------------------------------

    for txn_id, records in ledger_index.items():

        if (
            txn_id not in processed_ledger_ids
            and txn_id not in bank_index
        ):

            for ledger in records:

                if len(records) > 1:
                    add_result(
                        ledger,
                        None,
                        "NEEDS_INVESTIGATION",
                        (
                            "Conflicting ledger records have "
                            "no bank reference."
                        )
                    )

                else:
                    add_result(
                        ledger,
                        None,
                        "MISSING_IN_BANK",
                        (
                            "Ledger transaction has no "
                            "corresponding bank reference."
                        )
                    )

    # --------------------------------------------------
    # STEP 4: GENERATE RECONCILIATION SUMMARY
    # --------------------------------------------------

    summary = Counter(
        item["status"] for item in results
    )

    return {
        "results": results,
        "summary": dict(sorted(summary.items())),
        "total_results": len(results)
    }


def save_reconciliation_report(reconciliation):
    """Save detailed reconciliation and summary CSV files."""

    project_root = Path(__file__).resolve().parents[2]

    output_dir = project_root / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    results = reconciliation["results"]

    results_path = output_dir / "reconciliation_results.csv"
    summary_path = output_dir / "reconciliation_summary.csv"

    fields = [
        "bank_ref",
        "ledger_ref",
        "ledger_amount",
        "bank_amount",
        "ledger_account",
        "bank_account",
        "ledger_date",
        "bank_date",
        "ledger_currency",
        "bank_currency",
        "status",
        "notes"
    ]

    with results_path.open(
        "w", newline="", encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fields,
            lineterminator="\n"
        )

        writer.writeheader()
        writer.writerows(results)

    with summary_path.open(
        "w", newline="", encoding="utf-8"
    ) as file:

        writer = csv.writer(
            file,
            lineterminator="\n"
        )

        writer.writerow(["Status", "Count"])

        for status, count in sorted(
            reconciliation["summary"].items()
        ):
            writer.writerow([status, count])

    return results_path, summary_path
