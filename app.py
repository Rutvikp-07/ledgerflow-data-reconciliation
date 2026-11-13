
import sys
import csv
import html
import io
import tempfile
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent
SOURCE_DIR = PROJECT_ROOT / "src" / "ledgerflow"
sys.path.insert(0, str(SOURCE_DIR))

from pipeline import run_quality_pipeline


st.set_page_config(
    page_title="LedgerFlow Dashboard",
    page_icon="📊",
    layout="wide"
)


def read_csv_file(path):
    with open(path, "r", newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def render_table(records):
    if not records:
        st.info("No records available.")
        return

    columns = list(records[0].keys())

    content = [
        "<div style='overflow-x:auto'><table style='width:100%;"
        "border-collapse:collapse;font-size:13px;'>"
    ]

    content.append("<tr>")
    for column in columns:
        content.append(
            "<th style='padding:9px;border:1px solid #888;'>"
            + html.escape(str(column)) + "</th>"
        )
    content.append("</tr>")

    for record in records:
        content.append("<tr>")
        for column in columns:
            value = html.escape(str(record.get(column, "")))
            content.append(
                "<td style='padding:8px;border:1px solid #888;'>"
                + value + "</td>"
            )
        content.append("</tr>")

    content.append("</table></div>")

    st.markdown("".join(content), unsafe_allow_html=True)


def render_bars(data, heading):
    st.subheader(heading)

    maximum = max(data.values(), default=1)

    for label, value in data.items():
        st.write(f"**{label}: {value}**")
        st.progress(value / maximum if maximum else 0)


def create_csv(records):
    if not records:
        return ""

    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=list(records[0].keys()),
        lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(records)
    return output.getvalue()


# HEADER

st.title("📊 LedgerFlow")
st.caption("Financial Data Quality & Reconciliation Platform")

st.sidebar.title("LedgerFlow")

# FILE UPLOADS

st.sidebar.header("Input Files")

ledger_upload = st.sidebar.file_uploader(
    "Upload Company Ledger (CSV)",
    type=["csv"],
    key="ledger_upload"
)

bank_upload = st.sidebar.file_uploader(
    "Upload Bank Statement (JSON)",
    type=["json"],
    key="bank_upload"
)

st.sidebar.caption(
    "Leave a file empty to use the existing sample input."
)

if ledger_upload:
    st.sidebar.success(f"Ledger selected: {ledger_upload.name}")

if bank_upload:
    st.sidebar.success(f"Bank selected: {bank_upload.name}")


# NAVIGATION

page = st.sidebar.radio(
    "Navigation",
    [
        "Overview",
        "Data Quality",
        "Reconciliation",
        "Anomalies",
        "Data Explorer",
        "Downloads"
    ]
)


# RUN PIPELINE

if st.sidebar.button("Run Data Pipeline", type="primary"):

    try:
        with st.spinner("Processing financial data..."):

            # Temporary files are automatically removed after processing.
            with tempfile.TemporaryDirectory() as temp_directory:

                temp_directory = Path(temp_directory)

                ledger_path = None
                bank_path = None

                if ledger_upload:
                    ledger_path = temp_directory / "uploaded_ledger.csv"
                    ledger_path.write_bytes(ledger_upload.getvalue())

                if bank_upload:
                    bank_path = temp_directory / "uploaded_bank.json"
                    bank_path.write_bytes(bank_upload.getvalue())

                result = run_quality_pipeline(
                    ledger_path=ledger_path,
                    bank_path=bank_path
                )

            st.session_state["pipeline_result"] = result

            st.session_state["input_files"] = {
                "ledger": (
                    ledger_upload.name
                    if ledger_upload
                    else "Default sample ledger"
                ),
                "bank": (
                    bank_upload.name
                    if bank_upload
                    else "Default sample bank statement"
                )
            }

        st.sidebar.success("Pipeline completed successfully!")

    except Exception as error:
        st.session_state.pop("pipeline_result", None)
        st.sidebar.error(f"Pipeline failed: {error}")


# CHECK PIPELINE RESULT

if "pipeline_result" not in st.session_state:
    st.info("Upload your files or use the default samples, then run the pipeline.")
    st.stop()


result = st.session_state["pipeline_result"]

validation = result["validation"]
duplicates = result["duplicates"]
quality = result["quality_report"]
reconciliation = result["reconciliation"]
anomalies = result["anomalies"]

processed_records = read_csv_file(
    result["exports"]["processed_csv"]
)

reconciliation_records = reconciliation["results"]
anomaly_records = anomalies["anomalies"]


# SHOW INPUT FILES USED

with st.expander("View input files used for this run"):
    input_files = st.session_state.get("input_files", {})
    st.write("Ledger:", input_files.get("ledger", "Unknown"))
    st.write("Bank statement:", input_files.get("bank", "Unknown"))


# OVERVIEW

if page == "Overview":

    st.header("Pipeline Overview")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Ledger Records", len(result["source_records"]))
    c2.metric("Bank Records", len(result["bank_records"]))
    c3.metric("Clean Records", len(validation["clean_records"]))
    c4.metric("Rejected Records", len(validation["rejected_records"]))

    st.divider()

    percentages = quality["validation_percentages"]

    q1, q2, q3 = st.columns(3)
    q1.metric("Clean", f'{percentages["clean"]}%')
    q2.metric("Flagged", f'{percentages["flagged"]}%')
    q3.metric("Rejected", f'{percentages["rejected"]}%')

    render_bars({
        "Clean": quality["validation"]["clean"],
        "Flagged": quality["validation"]["flagged"],
        "Rejected": quality["validation"]["rejected"]
    }, "Data Quality Distribution")

    render_bars(
        reconciliation["summary"],
        "Reconciliation Status"
    )


# DATA QUALITY

elif page == "Data Quality":

    st.header("Data Quality Analysis")

    c1, c2, c3 = st.columns(3)

    c1.metric("Clean", len(validation["clean_records"]))
    c2.metric("Flagged", len(validation["flagged_records"]))
    c3.metric("Rejected", len(validation["rejected_records"]))

    st.divider()

    st.subheader("Duplicate Detection")

    d1, d2 = st.columns(2)

    d1.metric(
        "Exact Duplicate Rows Removed",
        duplicates["exact_duplicate_rows_removed"]
    )

    d2.metric(
        "Conflicting Duplicate Groups",
        len(duplicates["conflicting_duplicates"])
    )

    st.subheader("Warning Reasons")
    st.json(quality["warning_reasons"])

    st.subheader("Rejection Reasons")
    st.json(quality["rejection_reasons"])


# RECONCILIATION

elif page == "Reconciliation":

    st.header("Bank Reconciliation")

    statuses = sorted({
        record.get("status", "")
        for record in reconciliation_records
    } - {""})

    selected_status = st.selectbox(
        "Filter by status",
        ["ALL"] + statuses
    )

    filtered = [
        record for record in reconciliation_records
        if selected_status == "ALL"
        or record.get("status") == selected_status
    ]

    st.metric("Displayed Transactions", len(filtered))
    render_table(filtered)

    st.download_button(
        "Download Filtered Reconciliation CSV",
        create_csv(filtered),
        file_name="filtered_reconciliation.csv",
        mime="text/csv"
    )


# ANOMALIES

elif page == "Anomalies":

    st.header("Anomaly Detection")

    st.metric("Total Anomalies", anomalies["total_anomalies"])

    render_bars(
        anomalies["summary"],
        "Anomaly Rule Summary"
    )

    if anomaly_records:

        rules = sorted({
            record["rule"] for record in anomaly_records
        })

        selected_rule = st.selectbox(
            "Filter by rule",
            ["ALL"] + rules
        )

        filtered = [
            record for record in anomaly_records
            if selected_rule == "ALL"
            or record["rule"] == selected_rule
        ]

        render_table(filtered)

    else:
        st.success("No anomalies detected.")


# DATA EXPLORER

elif page == "Data Explorer":

    st.header("Processed Ledger Explorer")

    st.metric("Processed Transactions", len(processed_records))

    categories = sorted({
        record.get("category", "")
        for record in processed_records
    } - {""})

    selected_categories = st.multiselect(
        "Filter by category",
        categories,
        default=categories
    )

    search_id = st.text_input("Search Transaction ID")

    filtered = [
        record for record in processed_records
        if record.get("category", "") in selected_categories
        and search_id.lower() in record.get("txn_id", "").lower()
    ]

    st.write(f"Showing {len(filtered)} transactions")
    render_table(filtered)

    st.download_button(
        "Download Filtered Ledger CSV",
        create_csv(filtered),
        file_name="filtered_ledger.csv",
        mime="text/csv"
    )


# DOWNLOADS

elif page == "Downloads":

    st.header("Download Reports")

    files = {
        "Processed Ledger CSV": result["exports"]["processed_csv"],
        "Processed Ledger JSON": result["exports"]["processed_json"],
        "Rejected Ledger JSON": result["exports"]["rejected_json"],
        "Quality Report JSON": PROJECT_ROOT / "outputs" / "quality_report.json",
        "Quality Report CSV": PROJECT_ROOT / "outputs" / "quality_report.csv",
        "Anomaly Report CSV": result["anomaly_path"],
        "Reconciliation Results CSV": result["reconciliation_paths"][0],
        "Reconciliation Summary CSV": result["reconciliation_paths"][1],
        "Summary by Date CSV": result["summaries"]["date_summary"],
        "Summary by Category CSV": result["summaries"]["category_summary"],
        "Summary by Status CSV": result["summaries"]["status_summary"]
    }

    for label, path in files.items():

        path = Path(path)

        if path.exists():
            st.download_button(
                f"Download {label}",
                path.read_bytes(),
                file_name=path.name,
                mime="application/octet-stream",
                key=f"download_{label}"
            )
        else:
            st.warning(f"Missing report: {path.name}")


st.divider()
st.caption("LedgerFlow | Financial Data Quality & Reconciliation")
