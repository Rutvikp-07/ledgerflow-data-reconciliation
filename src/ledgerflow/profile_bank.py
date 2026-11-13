from ingestion import load_bank

bank = load_bank("../../data/raw/bank_statement.json")

# 1. Total number of records
print("Total Bank Records:", len(bank))

# 2. Column names
print("\nColumn Names:")
print(bank[0].keys())

# 3. Data types of each column
print("\nData Types:")
for column, value in bank[0].items():
    print(column, ":", type(value).__name__)

# 4. First five records
print("\nFirst 5 Bank Records:")
for record in bank[:5]:
    print(record)




# 5. Find missing values in each column

print("\nMissing Values:")

columns = bank[0].keys()

for column in columns:
    missing_count = 0

    for record in bank:
        value = record[column]

        if value is None or str(value).strip() == "":
            missing_count += 1

    print(f"{column}: {missing_count}")


# 6. Display records containing missing values

print("\nRecords with Missing Values:")

for record in bank:
    for column, value in record.items():

        if value is None or str(value).strip() == "":
            print(record)
            break



# 7. Investigate missing ledger references

print("\nMissing Ledger Reference Analysis:")

bank_only_count = 0
unlinked_count = 0

for record in bank:

    ledger_ref = record["ledger_ref"].strip()

    if ledger_ref == "":

        if record["memo"].strip().lower() == "bank-only item":
            bank_only_count += 1
        else:
            unlinked_count += 1

print("Explicit Bank-Only Items:", bank_only_count)
print("Other Records Without Ledger Reference:", unlinked_count)
print("Total Missing Ledger References:", bank_only_count + unlinked_count)




# 8. Find duplicate bank references

print("\nDuplicate Bank References:")

bank_ref_groups = {}

for record in bank:
    bank_ref = record["bank_ref"].strip()

    if bank_ref not in bank_ref_groups:
        bank_ref_groups[bank_ref] = []

    bank_ref_groups[bank_ref].append(record)


duplicate_bank_refs = {}

for bank_ref, records in bank_ref_groups.items():

    if len(records) > 1:
        duplicate_bank_refs[bank_ref] = records

        print(
            bank_ref,
            "| Occurrences:",
            len(records)
        )

print("\nNumber of Duplicate Bank References:", len(duplicate_bank_refs))





# 9. Find duplicate ledger references

print("\nDuplicate Ledger References:")

ledger_ref_groups = {}

for record in bank:
    ledger_ref = record["ledger_ref"].strip()

    # Ignore blank references
    if ledger_ref == "":
        continue

    if ledger_ref not in ledger_ref_groups:
        ledger_ref_groups[ledger_ref] = []

    ledger_ref_groups[ledger_ref].append(record)


duplicate_ledger_refs = {}

for ledger_ref, records in ledger_ref_groups.items():

    if len(records) > 1:
        duplicate_ledger_refs[ledger_ref] = records

        print("\nLedger Reference:", ledger_ref)
        print("Occurrences:", len(records))

        for record in records:
            print(record)


print("\nNumber of Duplicate Ledger References:", len(duplicate_ledger_refs))



# 9. Analyze bank date formats

print("\nBank Date Format Analysis:")

date_formats = {}

for record in bank:
    date_value = record["posted_date"].strip()

    if len(date_value) == 10 and date_value[4] == "-" and date_value[7] == "-":
        date_format = "YYYY-MM-DD"
    else:
        date_format = "OTHER / UNEXPECTED FORMAT"

    date_formats[date_format] = date_formats.get(date_format, 0) + 1

for date_format, count in date_formats.items():
    print(date_format, ":", count)





from decimal import Decimal, InvalidOperation

# 10. Analyze bank transaction amounts

print("\nBank Amount Analysis:")

valid_amounts = []
invalid_amounts = []

for record in bank:
    amount = record["amount"].strip()

    try:
        numeric_amount = Decimal(amount)
        valid_amounts.append(numeric_amount)

    except InvalidOperation:
        invalid_amounts.append(record)


zero_count = sum(1 for amount in valid_amounts if amount == 0)
negative_count = sum(1 for amount in valid_amounts if amount < 0)
positive_count = sum(1 for amount in valid_amounts if amount > 0)

print("Total Records:", len(bank))
print("Valid Numeric Amounts:", len(valid_amounts))
print("Invalid Amounts:", len(invalid_amounts))
print("Zero Amounts:", zero_count)
print("Negative Amounts:", negative_count)
print("Positive Amounts:", positive_count)

if invalid_amounts:
    print("\nRecords with Invalid Amounts:")
    for record in invalid_amounts:
        print(record)




# 11. Analyze bank currencies

print("\nBank Currency Analysis:")

currency_counts = {}

for record in bank:
    currency = record["currency"].strip()

    currency_counts[currency] = currency_counts.get(currency, 0) + 1

for currency, count in currency_counts.items():
    print(currency, ":", count)

print("\nTotal Unique Currencies:", len(currency_counts))





# 12. Analyze bank memo values

print("\nBank Memo Analysis:")

memo_counts = {}

for record in bank:
    memo = record["memo"].strip()

    memo_counts[memo] = memo_counts.get(memo, 0) + 1

for memo, count in sorted(memo_counts.items(), key=lambda item: item[1], reverse=True):
    print(memo, ":", count)

print("\nTotal Unique Memo Values:", len(memo_counts))

