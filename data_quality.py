import hashlib
import pandas as pd


def check_data_quality(df, file_bytes):
    return {
        "total_rows": len(df),
        "unique_journeys": df["JourneyId"].nunique(),
        "duplicate_rows": int(df.duplicated().sum()),
        "missing_values": df.isna().sum(),
        "file_hash": hashlib.sha256(file_bytes).hexdigest(),
    }


def detect_data_issues(df):
    issues = {}

    required = ["DateTime", "Transaction", "Product", "Amount"]

    issues["missing_required_values"] = int(
        df[required].isna().sum().sum()
    )

    amounts = pd.to_numeric(
        df["Amount"].astype(str).str.replace("$", "", regex=False),
        errors="coerce"
    )
    issues["invalid_amounts"] = int(amounts.isna().sum())

    dates = pd.to_datetime(
        df["DateTime"],
        format="%b-%d-%Y %I:%M %p",
        errors="coerce"
    )
    issues["invalid_dates"] = int(dates.isna().sum())

    return issues
