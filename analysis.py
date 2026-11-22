import pandas as pd

REQUIRED_COLUMNS = [
    "DateTime",
    "Transaction",
    "Product",
    "Amount",
    "JourneyId"
]

def validate_csv(df):
    missing = [
        col for col in REQUIRED_COLUMNS
        if col not in df.columns
    ]

    if missing:
        return False, missing

    return True, []

def aggregate_journeys(df):

    df = df.copy()

    df["Amount"] = pd.to_numeric(
        df["Amount"]
        .astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip(),
        errors="coerce"
    )
    journeys = df.groupby("JourneyId").agg(
        product=("Product", "first"),
        transaction_count=("Amount", "count"),
        total_amount=("Amount", "sum")
    ).reset_index()

    journeys["journey_cost"] = -journeys["total_amount"]

    return journeys

def calculate_stored_value_cost(journeys):

    stored_value = journeys[
        journeys["product"] == "Stored Value"
    ].copy()

    total_cost = stored_value["journey_cost"].sum()

    return total_cost
