
from ingestion import load_ledger

ledger = load_ledger("../../data/raw/company_ledger.csv")

# 1. Total number of records
print("Total Records:", len(ledger))

# 2. Column names
print("\nColumn Names:")
print(ledger[0].keys())

# 3. Data types of each column
print("\nData Types:")
for column, value in ledger[0].items():
    print(column, ":", type(value).__name__)

# 4. First 5 records
print("\nFirst 5 Records:")
for record in ledger[:5]:
    print(record)



# 5. Find missing values in each column

print("\nMissing Values:")

columns = ledger[0].keys()

for column in columns:
    missing_count = 0

    for record in ledger:
        value = record[column]

        if value is None or value.strip() == "":
            missing_count += 1

    print(f"{column}: {missing_count}")




# 6. Display records containing missing values

print("\nRecords with Missing Values:")

for record in ledger:
    for column, value in record.items():
        if value is None or value.strip() == "":
            print(record)
            break





# 7. Find duplicate transaction IDs

print("\nDuplicate Transaction IDs:")

transaction_ids = []
duplicate_ids = set()

for record in ledger:
    txn_id = record["txn_id"]

    if txn_id in transaction_ids:
        duplicate_ids.add(txn_id)
    else:
        transaction_ids.append(txn_id)

print("Duplicate IDs:", duplicate_ids)
print("Number of duplicate IDs:", len(duplicate_ids))




# 8. Find exact duplicate records

print("\nExact Duplicate Records:")

seen_records = set()
duplicate_count = 0

for record in ledger:
    record_key = tuple(record.items())

    if record_key in seen_records:
        duplicate_count += 1
        print(record)
    else:
        seen_records.add(record_key)

print("Number of exact duplicate records:", duplicate_count)




# 9. Inspect all records with duplicate transaction IDs

print("\nDetailed Duplicate Transaction Records:")

for txn_id in duplicate_ids:
    print(f"\nTransaction ID: {txn_id}")

    for record in ledger:
        if record["txn_id"] == txn_id:
            print(record)



#
# 10. Classify transaction records

print("\nDuplicate Classification Report:")

grouped_transactions = {}

# Group records by transaction ID
for record in ledger:
    txn_id = record["txn_id"]

    if txn_id not in grouped_transactions:
        grouped_transactions[txn_id] = []

    grouped_transactions[txn_id].append(record)


# Initialize classification counters
classification_counts = {
    "UNIQUE": 0,
    "EXACT_DUPLICATE": 0,
    "CONFLICTING_DUPLICATE": 0
}


# Classify each transaction ID
for txn_id, records in grouped_transactions.items():

    if len(records) == 1:
        status = "UNIQUE"

    else:
        first_record = records[0]

        if all(record == first_record for record in records):
            status = "EXACT_DUPLICATE"
        else:
            status = "CONFLICTING_DUPLICATE"

    # Update classification count
    classification_counts[status] += 1

    # Display duplicate groups
    if status != "UNIQUE":
        print(
            txn_id,
            ":",
            status,
            "| Occurrences:",
            len(records)
        )


# Display summary
print("\nClassification Summary:")

for status, count in classification_counts.items():
    print(f"{status}: {count}")

print("\nTotal Transaction IDs:", len(grouped_transactions))
