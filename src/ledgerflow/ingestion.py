
import csv
import json


def load_ledger(file_path):
    company = []

    with open(file_path, "r", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            company.append(row)

    return company


def load_bank(file_path):
    with open(file_path, "r") as file:
        data = json.load(file)

    return data["records"]


# Optional standalone testing
if __name__ == "__main__":

    ledger = load_ledger("../../data/raw/company_ledger.csv")
    bank = load_bank("../../data/raw/bank_statement.json")

    print("Company Ledger Records:", len(ledger))
    print("Bank Statement Records:", len(bank))

    if ledger:
        print("Ledger Sample:", ledger[0])

    if bank:
        print("Bank Sample:", bank[0])
