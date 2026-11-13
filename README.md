

\# LedgerFlow – Financial Data Reconciliation System



\## 1. Project Overview



LedgerFlow is a Python-based financial data reconciliation project that compares company ledger transactions with bank statement records.



The system processes two independent data sources, profiles their quality, identifies duplicates and missing records, and classifies transactions based on reconciliation results.



The goal is to make financial discrepancies easier to identify, investigate, and audit.



\## 2. Key Features



\- Load company ledger data from CSV.

\- Load bank statement data from JSON.

\- Profile source data and identify missing values.

\- Detect exact and conflicting duplicate ledger transaction IDs.

\- Detect duplicate bank references.

\- Normalize transaction amounts using Python Decimal.

\- Match transactions using ledger references.

\- Identify amount, account, and currency mismatches.

\- Identify missing and unlinked transactions.

\- Flag duplicate records for investigation.

\- Generate detailed reconciliation and summary CSV reports.



\## 3. Technology Stack



\- Python

\- CSV

\- JSON

\- Decimal

\- Collections

\- Git and GitHub



The project currently uses Python's standard library and does not require third-party packages.



\## 4. Project Structure



```text

LedgerFlow/

│

├── config/

│

├── data/

│   ├── raw/

│   └── processed/

│

├── outputs/

│   ├── reconciliation\_results.csv

│   └── reconciliation\_summary.csv

│

├── logs/

│

├── src/

│   └── ledgerflow/

│       ├── ingestion.py

│       ├── profile\_ledger.py

│       ├── profile\_bank.py

│       └── reconciliation.py

│

├── tests/

├── scripts/

├── .gitignore

└── README.md

```



\## 5. Data Sources



\### Company Ledger (CSV)



Contains company transaction information.



Main fields:



\- txn\_id

\- account\_id

\- txn\_date

\- amount

\- currency

\- category

\- merchant

\- description



\### Bank Statement (JSON)



Contains bank transaction information.



Main fields:



\- bank\_ref

\- ledger\_ref

\- account

\- posted\_date

\- amount

\- currency

\- memo



The two sources are processed independently. Their record counts are not expected to be identical.



\## 6. Data Quality Profiling



The source profiling stage examines:



\- Total records and columns.

\- Data types.

\- Missing values.

\- Duplicate transaction identifiers.

\- Duplicate bank references.

\- Date formats.

\- Amount validity.

\- Currency distribution.

\- Unlinked bank transactions.



\### Profiling Findings



Company Ledger:

\- Total records: 1,232

\- Unique transaction IDs: 1,218

\- Duplicate transaction ID groups: 14

\- Exact duplicate groups: 10

\- Conflicting duplicate groups: 4



Bank Statement:

\- Total records: 1,180

\- Missing ledger references: 66

\- Explicit bank-only records: 25

\- Other unlinked records: 41

\- Duplicate bank references: 0



\## 7. Reconciliation Logic



The reconciliation engine uses transaction references to identify corresponding records.



It performs the following checks:



1\. Identifies bank transactions without ledger references.

2\. Identifies explicitly marked bank-only transactions.

3\. Checks for duplicate bank references.

4\. Checks whether a bank reference exists in the company ledger.

5\. Flags duplicate ledger transaction IDs.

6\. Compares transaction amounts.

7\. Compares account identifiers.

8\. Compares currencies.

9\. Identifies ledger transactions missing from the bank statement.



Amounts are converted to Decimal before comparison to avoid floating-point precision problems.



Duplicate ledger candidates are included in the detailed report for investigation.



\## 8. Reconciliation Results



The current execution produced the following results:



| Status | Count |

|---|---:|

| MATCHED | 1,079 |

| AMOUNT\_MISMATCH | 10 |

| ACCOUNT\_MISMATCH | 4 |

| INVALID\_AMOUNT | 4 |

| MISSING\_IN\_BANK | 107 |

| MISSING\_IN\_LEDGER | 5 |

| EXPLICIT\_BANK\_ONLY | 25 |

| UNLINKED\_BANK\_TRANSACTION | 41 |

| NEEDS\_INVESTIGATION | 16 |

| \*\*Total report rows\*\* | \*\*1,291\*\* |



The total report row count is higher than either source count because the report also includes ledger-side transactions that have no corresponding bank record.



The status counts represent reconciliation report rows, not unique source transactions.



\## 9. Generated Reports



\### reconciliation\_results.csv



Contains transaction-level reconciliation details, including:



\- Bank reference

\- Ledger reference

\- Ledger amount

\- Bank amount

\- Account information

\- Transaction dates

\- Currency

\- Duplicate ledger candidates

\- Reconciliation status

\- Investigation notes



\### reconciliation\_summary.csv



Contains the count of records classified under each reconciliation status.



\## 10. How to Run



\### Step 1: Clone the repository



```bash

git clone https://github.com/Rutvikp-07/ledgerflow-data-reconciliation.git

```



\### Step 2: Navigate to the project



```bash

cd ledgerflow-data-reconciliation

```



\### Step 3: Create and activate a virtual environment



Windows:



```bash

python -m venv .venv

.venv\\Scripts\\activate

```



\### Step 4: Add the input files



Place the source files in:



```text

data/raw/

```



Expected filenames:



\- company\_ledger.csv

\- bank\_statement.json



\### Step 5: Run reconciliation



Navigate to:



```bash

cd src/ledgerflow

```



Execute:



```bash

python reconciliation.py

```



The generated reports will be available in the `outputs/` directory.



\## 11. Current Limitations



\- Unlinked bank transactions are identified but are not automatically matched using secondary fields.

\- Transaction dates are included in reports but are not currently used as a reconciliation matching condition.

\- Duplicate ledger transactions require manual investigation.

\- The current implementation uses transaction references as the primary matching key.



\## 12. Future Improvements



\- Secondary matching using amount, account, merchant, and transaction date.

\- Date normalization and date-tolerance rules.

\- Automated test coverage.

\- Structured logging.

\- Configurable reconciliation rules.

\- Improved reporting and audit history.



\## 13. Project Purpose



LedgerFlow was developed as a practical Data Engineering project to explore data ingestion, data profiling, data quality checks, duplicate detection, transaction reconciliation, and report generation using Python.



