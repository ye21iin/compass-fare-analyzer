from pdf_report import generate_pdf
import streamlit as st
import pandas as pd

from analysis import validate_csv
from analysis_streamlit import run_analysis
from data_quality import check_data_quality, detect_data_issues

st.set_page_config(page_title="Compass Card Fare Analyzer", layout="wide")
st.title("🚆 Compass Card Fare Analyzer")

uploaded_file = st.file_uploader("Upload your Compass Card CSV", type=["csv"])

if uploaded_file is not None:
    try:
        file_bytes = uploaded_file.getvalue()
        df = pd.read_csv(uploaded_file)
        is_valid, missing = validate_csv(df)

        if not is_valid:
            st.error(f"Missing columns: {missing}")
        else:
            st.success("Valid Compass Card CSV!")

            quality = check_data_quality(df, file_bytes)

            st.subheader("Data Quality Dashboard")
            c1, c2, c3 = st.columns(3)
            c1.metric("Transactions", quality["total_rows"])
            c2.metric("Unique Journeys", quality["unique_journeys"])
            c3.metric("Duplicate Rows", quality["duplicate_rows"])

            st.write("Missing Values by Column")
            missing = quality["missing_values"]
            st.dataframe(
                missing.rename("Missing Count").reset_index()
                .rename(columns={"index": "Column"}),
                hide_index=True
            )
            st.caption(f"SHA-256: {quality['file_hash']}")

            st.subheader("Transactions Without JourneyId")

            missing_journeys = df[df["JourneyId"].isna()]

            st.write(f"Total: {len(missing_journeys)} transactions")

            st.dataframe(
                missing_journeys.groupby(
                    ["Transaction", "Product"],
                    dropna=False
                ).size().reset_index(name="Count"),
                hide_index=True
            )

            # Classify transactions without JourneyId
            non_journey = df[df["JourneyId"].isna()].copy()

            known_patterns = (
                "AutoLoaded",
                "Loaded at ",
                "Purchase at "
            )

            expected = non_journey["Transaction"].fillna("").str.startswith(
                known_patterns
            )

            normal_count = int(expected.sum())
            unexpected_count = int((~expected).sum())

            st.subheader("Data Quality Classification")
            c1, c2 = st.columns(2)
            c1.metric("Expected Non-Journey Transactions", normal_count)
            c2.metric("Unclassified Transactions", unexpected_count)

            if unexpected_count:
                st.warning(
                    f"{unexpected_count} transactions require review."
                )
                st.dataframe(non_journey.loc[~expected])
            else:
                st.success("All missing JourneyIds are explained.")

            st.subheader("Data Issue Detection")

            issues = detect_data_issues(df)

            c1, c2, c3 = st.columns(3)
            c1.metric("Missing Required Values", issues["missing_required_values"])
            c2.metric("Invalid Amounts", issues["invalid_amounts"])
            c3.metric("Invalid Dates", issues["invalid_dates"])

            if any(issues.values()):
                st.warning("Potential data issues detected.")
            else:
                st.success("No data format issues detected.")

            if any(issues.values()):
                st.error("Analysis stopped: Please fix the CSV data issues.")
                st.stop()

            results = run_analysis(df)
            journeys = results["journeys"]

            pdf_bytes = generate_pdf(results)

            st.download_button(
                label="📄 Download PDF Report",
                data=pdf_bytes,
                file_name="compass_fare_report.pdf",
                mime="application/pdf"
            )



            st.subheader("Overview")

            total_journeys = len(journeys)
            total_cost = results["total_expenditure"]
            average_cost = total_cost / total_journeys if total_journeys else 0

            c1, c2, c3 = st.columns(3)
            c1.metric("Total Journeys", total_journeys)
            c2.metric("Total Expenditure", f"${total_cost:.2f}")
            c3.metric("Average Cost per Journey", f"${average_cost:.2f}")


            stored_value_cost = (
                results["monthly_expenditure"]["StoredValueCost"].sum()
            )
            st.metric(
                "Stored Value Total Cost",
                f"${stored_value_cost:.2f}"
            )

            st.subheader("Journey Analysis")
            st.dataframe(journeys)

            st.subheader("Monthly Expenditure")
            st.dataframe(results["monthly_expenditure"])
            st.subheader("Monthly Spending Chart")

            monthly_chart = results["monthly_expenditure"].assign(Month=lambda x: x["Month"].astype(str)).set_index("Month")

            st.bar_chart(
                monthly_chart["TotalExpenditure"],
                y_label="Expenditure (CAD)",
                x_label="Month"
            )




            st.subheader("Monthly Journey Frequency")

            journey_chart = results["monthly_expenditure"].copy()
            journey_chart["Month"] = journey_chart["Month"].astype(str)

            st.bar_chart(
                journey_chart,
                x="Month",
                y="JourneyCount",
                x_label="Month",
                y_label="Number of Journeys"
            )

            st.subheader("Fare Efficiency")
            st.dataframe(results["fare_efficiency"])
            st.subheader("Cost per Journey by Month")

            efficiency_chart = results["monthly_expenditure"].copy()
            efficiency_chart["Month"] = efficiency_chart["Month"].astype(str)

            efficiency_chart["CostPerJourney"] = (
                efficiency_chart["TotalExpenditure"]
                / efficiency_chart["JourneyCount"].replace(0, float("nan"))
            )

            st.bar_chart(
                efficiency_chart,
                x="Month",
                y="CostPerJourney",
                x_label="Month",
                y_label="Average Cost per Journey (CAD)"
            )


    except Exception as e:
        st.exception(e)
