# LedgerFlow – Financial Data Quality and Reconciliation System

## 1. Project Overview

LedgerFlow is a Python-based financial data engineering project that processes company ledger transactions and bank statement records.

It provides an end-to-end pipeline for data ingestion, normalization, data quality validation, duplicate classification, anomaly detection, transaction reconciliation, reporting, and dashboard-based exploration.

The project is designed to make financial discrepancies easier to identify, explain, and investigate.

## 2. Key Features

- Load company ledger data from CSV.
- Load bank statement data from JSON.
- Upload custom CSV and JSON files through the dashboard.
- Normalize transaction IDs, dates, categories, and monetary values.
- Validate records using configurable JSON quality rules.
- Classify records as CLEAN, FLAGGED, or REJECTED.
- Detect exact and conflicting duplicate transactions.
- Detect explainable anomalies using configurable rules.
- Reconcile ledger and bank transactions using primary and secondary matching.
- Identify missing, unmatched, and inconsistent transactions.
- Generate quality, anomaly, reconciliation, and summary reports.
- Explore results through an interactive Streamlit dashboard.
- Download generated reports.

## 3. Technology Stack

- Python
- CSV and JSON
- Decimal
- Collections
- Streamlit
- HTML
- Git and GitHub
- Python unittest

The core data processing and testing logic primarily uses Python's standard library. Streamlit is used for the dashboard.

## 4. Project Structure

```text
LedgerFlow/
├── config/
│   └── quality_rules.json
├── data/
│   ├── raw/
│   └── processed/
├── outputs/
├── logs/
├── src/
│   └── ledgerflow/
│       ├── ingestion.py
│       ├── normalization.py
│       ├── quality.py
│       ├── duplicates.py
│       ├── quality_report.py
│       ├── anomalies.py
│       ├── reconciliation.py
│       ├── exports.py
│       ├── summaries.py
│       └── pipeline.py
├── tests/
├── app.py
├── run.py
├── requirements.txt
├── .gitignore
└── README.md
```

## 5. Data Sources

### Company Ledger (CSV)

Contains company transaction information, including:

- txn_id
- account_id
- txn_date
- amount
- currency
- category
- merchant
- description

### Bank Statement (JSON)

Contains bank transaction information, including:

- bank_ref
- ledger_ref
- account
- posted_date
- amount
- currency
- memo

The two sources are processed independently. Their record counts are not expected to be identical.

## 6. Data Quality and Validation

LedgerFlow validates records using configurable rules stored in:

`config/quality_rules.json`

Validation includes:

- Missing transaction IDs.
- Missing account identifiers.
- Missing transaction dates.
- Invalid dates.
- Invalid monetary values.
- Unsupported currencies.
- Missing transaction categories.

Records are classified into three categories:

- CLEAN – Records that pass validation.
- FLAGGED – Records with warnings that require attention.
- REJECTED – Records with validation errors.

### Current sample dataset results

| Metric | Count |
|---|---:|
| Total ledger records | 1,232 |
| Clean records | 1,207 |
| Flagged records | 16 |
| Rejected records | 9 |

## 7. Duplicate Classification

LedgerFlow identifies duplicate transaction IDs and distinguishes between:

- Exact duplicates – Additional identical copies are removed.
- Conflicting duplicates – Records sharing an ID but containing different data are preserved for investigation.

### Current sample dataset results

| Metric | Count |
|---|---:|
| Exact duplicate groups | 10 |
| Exact duplicate rows removed | 10 |
| Conflicting duplicate groups | 4 |
| Conflicting duplicate rows | 8 |

Conflicting duplicates are retained rather than silently discarded.

## 8. Anomaly Detection

The anomaly detection module applies configurable rules to identify transactions that may require investigation.

Current rules include:

- High-value transactions.
- Future-dated transactions.
- Weekend transactions.

Each detected anomaly includes its transaction ID, rule, severity, description, and explanation.

An anomaly is a review indicator, not proof of fraud or an invalid transaction.

## 9. Reconciliation Logic

LedgerFlow compares normalized ledger and bank records.

### Primary matching

Transactions are first matched using their ledger reference.

### Secondary matching

When a usable ledger reference is unavailable, the system can search for a unique candidate using:

- Account information.
- Transaction amount.
- Currency.
- Merchant or memo information.
- Transaction date within the configured tolerance.

Ambiguous candidates are not automatically treated as matches.

The reconciliation engine also identifies:

- Amount mismatches.
- Account mismatches.
- Missing ledger transactions.
- Missing bank transactions.
- Explicit bank-only transactions.
- Unlinked bank transactions.
- Transactions requiring investigation.

Every non-matched result includes an explanation in the report.

Amounts are parsed using Python's Decimal to avoid floating-point comparison issues.

## 10. Current Reconciliation Results

The current sample dataset produced the following results:

| Status | Count |
|---|---:|
| ACCOUNT_MISMATCH | 4 |
| AMOUNT_MISMATCH | 10 |
| EXPLICIT_BANK_ONLY | 25 |
| MATCHED | 1,088 |
| MISSING_IN_BANK | 63 |
| MISSING_IN_LEDGER | 8 |
| NEEDS_INVESTIGATION | 4 |
| SECONDARY_MATCHED | 40 |
| UNLINKED_BANK_TRANSACTION | 1 |
| **Total report rows** | **1,243** |

These are reconciliation report rows, not a count of unique transactions in either source.

## 11. Generated Reports

### Processed data

- `data/processed/cleaned_ledger.csv`
- `data/processed/cleaned_ledger.json`
- `data/processed/rejected_ledger.json`

### Quality reports

- `outputs/quality_report.json`
- `outputs/quality_report.csv`

### Anomaly report

- `outputs/anomaly_report.csv`

### Reconciliation reports

- `outputs/reconciliation_results.csv`
- `outputs/reconciliation_summary.csv`

### Summary reports

- `outputs/summary_by_date.csv`
- `outputs/summary_by_category.csv`
- `outputs/summary_by_status.csv`

## 12. Streamlit Dashboard

The project includes a dashboard with the following pages:

- **Overview:** Key pipeline metrics and dataset summary.
- **Data Quality:** Validation results and quality breakdown.
- **Reconciliation:** Matching results and transaction discrepancies.
- **Anomalies:** Detected anomalies and explanations.
- **Data Explorer:** Explore transaction records.
- **Downloads:** Download generated reports.

The dashboard supports uploading a custom company ledger CSV and bank statement JSON file.

## 13. How to Run

### Step 1: Clone the repository

```bash
git clone https://github.com/Rutvikp-07/ledgerflow-data-reconciliation.git
```

### Step 2: Navigate to the project

```bash
cd ledgerflow-data-reconciliation
```

### Step 3: Create and activate a virtual environment

Windows:

```cmd
python -m venv .venv
.venv\Scripts\activate
```

### Step 4: Install dependencies

```cmd
python -m pip install -r requirements.txt
```

### Step 5: Run the complete data pipeline

From the project root:

```cmd
python run.py
```

### Step 6: Launch the dashboard

```cmd
streamlit run app.py
```

### Step 7: Run automated tests

```cmd
python -m unittest discover -s tests -v
```

## 14. Testing and Reliability

LedgerFlow includes automated unit and integration tests covering:

- Data ingestion.
- Data normalization.
- Data quality validation.
- Duplicate classification.
- Transaction reconciliation.
- Complete pipeline execution.

The current test suite contains **32 passing tests**.

The pipeline has also been checked for deterministic execution by comparing SHA-256 hashes of generated output files across consecutive runs.

## 15. Current Limitations

- The sample dataset is used for the default pipeline execution.
- Anomaly detection is rule-based rather than machine-learning-based.
- Ambiguous secondary matching candidates require investigation.
- Generated reports are refreshed when the pipeline runs; previous run outputs are not maintained as a separate audit history.
- Parquet export is not currently part of the required export workflow.

## 16. Future Improvements

- Add persistent run history and audit tracking.
- Expand configurable matching strategies.
- Add more data sources and file formats.
- Introduce additional quality and anomaly rules.
- Improve large-dataset processing.
- Add more detailed dashboard drill-down capabilities.

## 17. Project Purpose

LedgerFlow was developed as a practical Data Engineering project to demonstrate data ingestion, transformation, validation, duplicate handling, anomaly detection, reconciliation, automated testing, reporting, and dashboard development using Python.d date-tolerance rules.

\- Automated test coverage.

\- Structured logging.

\- Configurable reconciliation rules.

\- Improved reporting and audit history.



\## 13. Project Purpose



LedgerFlow was developed as a practical Data Engineering project to explore data ingestion, data profiling, data quality checks, duplicate detection, transaction reconciliation, and report generation using Python.



