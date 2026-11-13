from datetime import datetime
from decimal import Decimal, InvalidOperation


def normalize_transaction_id(value):
    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    return value.upper()


def normalize_category(value):
    if value is None:
        return None

    value = " ".join(str(value).split())

    if not value:
        return None

    return value.casefold()


def parse_amount(value):
    """Convert an amount into a finite Decimal safely."""
    if value is None or str(value).strip() == "":
        return None

    cleaned_value = str(value).replace("$", "").replace(",", "").strip()

    try:
        amount = Decimal(cleaned_value)

        if not amount.is_finite():
            raise ValueError(f"Invalid amount: {value}")

        return amount

    except InvalidOperation:
        raise ValueError(f"Invalid amount: {value}")


def parse_transaction_date(value):
    if value is None or str(value).strip() == "":
        return None

    value = str(value).strip()

    formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d %b %Y"
    ]

    for date_format in formats:
        try:
            return datetime.strptime(value, date_format).date()
        except ValueError:
            continue

    raise ValueError(f"Invalid transaction date: {value}")