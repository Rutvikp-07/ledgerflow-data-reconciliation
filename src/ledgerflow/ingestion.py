import csv

import json


def load_ledger(file_path):

    company=[]

    with open(file_path,"r",newline="")as file:
        reader=csv.DictReader(file)


        for row in reader:
           company.append(row)
    return company

ledger = load_ledger("../../data/raw/company_ledger.csv")

print(len(ledger))       # 1232
print(type(ledger[0]))   # <class 'dict'>
print(ledger[0])


def load_bank(file_path):
    with open(file_path,"r")as file:
        data=json.load(file)
        return data["records"]

bank = load_bank("../../data/raw/bank_statement.json")

print(len(bank))
print(type(bank[0]))
print(bank[0])