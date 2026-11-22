import pathlib
import pandas as pd

# ========================================


# ========================================


# ========================================


# ========================================


print(pd.__version__)

# ========================================

import os

os.listdir()

# ========================================


def run_analysis(df):
    def display(*args, **kwargs):
        pass

    df = df.copy()

    print("데이터 크기:", df.shape)
    print("\n컬럼명:")
    print(df.columns.tolist())

    print("\n첫 5행:")
    display(df.head(5))

    # ========================================

    print("=== Transaction 종류 ===")
    print(df["Transaction"].value_counts(dropna=False).to_string())

    print("\n=== Product 종류 ===")
    print(df["Product"].value_counts(dropna=False).to_string())

    print("\n=== LineItem 종류 ===")
    print(df["LineItem"].value_counts(dropna=False).to_string())

    print("\n=== Payment 종류 ===")
    print(df["Payment"].value_counts(dropna=False).to_string())

    # ========================================

    df.info()

    # ========================================

    df["Amount"].value_counts().head(20)


    # ========================================

    df[["DateTime", "Transaction", "Product", "Amount", "JourneyId"]].head(20)

    # ========================================

    df[df["JourneyId"].isna()][
        ["DateTime", "Transaction", "Product", "Amount", "BalanceDetails"]
    ]

    # ========================================

    clean_df = df.copy()

    # ========================================

    # 현재 DateTime은 str이므로 datetime type으로 변환
    clean_df["DateTime"] = pd.to_datetime(
        clean_df["DateTime"],
        format="%b-%d-%Y %I:%M %p",
        errors="coerce"
    )

    # ========================================

    ### Convert currency variables to numeric

    # Amount와 BalanceDetails의 $를 제거하고 numeric variables로 변환
    for col in ["Amount", "BalanceDetails"]:
        clean_df[col] = pd.to_numeric(
            clean_df[col].str.replace("$", "", regex=False),
            errors="coerce"
        )

    # ========================================

    # Validation

    print(clean_df[["DateTime", "Amount", "BalanceDetails"]].dtypes)

    print("\nMissing values after conversion:")
    print(
        clean_df[["DateTime", "Amount", "BalanceDetails"]]
        .isna()
        .sum()
    )

    print("\nNumber of observations:")
    print(len(clean_df))

    # ========================================

    # ==========================================
    # Step 4: Data Quality Validation
    # ==========================================

    # 1. Dataset dimensions
    print("=== Dataset Dimensions ===")
    print(f"Observations: {clean_df.shape[0]}")
    print(f"Variables: {clean_df.shape[1]}")

    # 2. Missing values
    print("\n=== Missing Values ===")
    print(clean_df.isna().sum())

    # 3. Exact duplicate observations
    print("\n=== Duplicate Observations ===")
    print("Number of exact duplicates:", clean_df.duplicated().sum())

    # 4. Date range
    print("\n=== Temporal Coverage ===")
    print("Start:", clean_df["DateTime"].min())
    print("End:", clean_df["DateTime"].max())

    # 5. Monetary variable range
    print("\n=== Amount Summary ===")
    print(clean_df["Amount"].describe())

    print("\n=== Balance Summary ===")
    print(clean_df["BalanceDetails"].describe())

    # 6. JourneyId completeness
    print("\n=== JourneyId Completeness ===")
    print("Missing JourneyId:", clean_df["JourneyId"].isna().sum())
    print("Non-missing JourneyId:", clean_df["JourneyId"].notna().sum())
    print("Unique JourneyId:", clean_df["JourneyId"].nunique())

    # 7. Product categories
    print("\n=== Product Categories ===")
    print(clean_df["Product"].value_counts())

    # 8. Check observations without JourneyId
    print("\n=== Observations Without JourneyId ===")
    display(
        clean_df.loc[
            clean_df["JourneyId"].isna(),
            ["DateTime", "Transaction", "Product",
             "Amount", "BalanceDetails"]
        ]
    )

    # ========================================

    product_timeline = (
        clean_df[
            clean_df["JourneyId"].notna()
        ]
        [["DateTime", "JourneyId", "Product"]]
        .drop_duplicates(subset=["JourneyId", "Product"])
        .sort_values("DateTime")
    )

    # July ~ September만 확인
    display(
        product_timeline[
            product_timeline["DateTime"].between(
                "2026-07-01",
                "2026-09-30 23:59:59"
            )
        ]
    )

    # ========================================

    monthly_pass_timeline = (
        clean_df[
            clean_df["JourneyId"].notna()
            & clean_df["Product"].isin([
                "1 Zone Monthly Pass",
                "2 Zone Monthly Pass"
            ])
        ]
        [["DateTime", "JourneyId", "Product"]]
        .drop_duplicates(subset=["JourneyId"])
        .sort_values("DateTime")
        .reset_index(drop=True)
    )

    monthly_pass_timeline["PreviousProduct"] = (
        monthly_pass_timeline["Product"].shift(1)
    )

    transition_2_to_1 = monthly_pass_timeline[
        (monthly_pass_timeline["PreviousProduct"] == "2 Zone Monthly Pass") &
        (monthly_pass_timeline["Product"] == "1 Zone Monthly Pass")
    ]

    display(transition_2_to_1)

    # ========================================

    clean_df["Month"] = clean_df["DateTime"].dt.to_period("M")

    monthly_product_usage = (
        clean_df[
            clean_df["JourneyId"].notna()
        ]
        .groupby(["Month", "Product"])["JourneyId"]
        .nunique()
        .unstack(fill_value=0)
    )

    display(monthly_product_usage)

    # ========================================

    fare_reference = pd.read_csv(
        pathlib.Path(__file__).resolve().parent / "fare_reference.csv",
        parse_dates=["effective_from", "effective_to"]
    )


    # Validate external fare reference
    required = [
        "effective_from", "effective_to", "fare_period",
        "stored_value_1_zone", "stored_value_2_zone",
        "stored_value_3_zone", "monthly_pass_1_zone",
        "monthly_pass_2_zone", "monthly_pass_3_zone",
        "yvr_addfare"
    ]

    if not set(required).issubset(fare_reference.columns):
        raise ValueError("Fare reference has missing columns.")

    if fare_reference[required].isna().any().any():
        raise ValueError("Fare reference contains missing values.")

    fare_columns = required[3:]
    fare_reference[fare_columns] = fare_reference[fare_columns].apply(
        pd.to_numeric, errors="raise"
    )

    if (fare_reference[fare_columns] < 0).any().any():
        raise ValueError("Fare reference contains negative fares.")

    fare_sorted = fare_reference.sort_values("effective_from")

    if (fare_sorted["effective_from"] > fare_sorted["effective_to"]).any():
        raise ValueError("Invalid fare date range.")

    previous_end = fare_sorted["effective_to"].shift()

    if (
        fare_sorted["effective_from"].iloc[1:].reset_index(drop=True)
        <= previous_end.iloc[1:].reset_index(drop=True)
    ).any():
        raise ValueError("Overlapping fare date ranges.")

    display(fare_reference)

    # ========================================

    import numpy as np

    clean_df["FarePeriod"] = np.where(
        clean_df["DateTime"] < fare_reference.loc[
            fare_reference["fare_period"] == "Post-increase",
            "effective_from"
        ].iloc[0],
        "Pre-increase",
        "Post-increase"
    )

    print(
        clean_df.groupby("FarePeriod")
        .agg(
            StartDate=("DateTime", "min"),
            EndDate=("DateTime", "max"),
            Observations=("DateTime", "size")
        )
    )

    # ========================================

    monthly_pass_cost = pd.DataFrame({
        "Month": pd.PeriodIndex([
            "2026-06",
            "2026-07",
            "2026-09",
            "2026-10"
        ], freq="M"),

        "FareProduct": [
            "2 Zone Monthly Pass",
            "2 Zone Monthly Pass",
            "1 Zone Monthly Pass",
            "1 Zone Monthly Pass"
        ],

        "PassCost": [
            149.25,   # June: pre-increase 2 Zone
            156.70,   # July: post-increase 2 Zone
            117.20,   # September: post-increase 1 Zone
            117.20    # October: post-increase 1 Zone
        ]
    })

    display(monthly_pass_cost)

    # ========================================

    # 6.1 Journey-Level Dataset
    journey_df = (
        clean_df[clean_df["JourneyId"].notna()]
        .groupby("JourneyId")
        .agg(
            JourneyStart=("DateTime", "min"),
            JourneyEnd=("DateTime", "max"),
            Product=("Product", "first"),
            NetAmount=("Amount", "sum"),
            TransactionCount=("Transaction", "count")
        )
        .reset_index()
    )

    # Net deduction을 양수 비용으로 표현
    journey_df["ObservedJourneyCost"] = -journey_df["NetAmount"]

    # 분석용 Month
    journey_df["Month"] = journey_df["JourneyStart"].dt.to_period("M")

    display(journey_df.head(10))


    # ========================================

    # 6.2 Validation
    print("Number of unique JourneyIds:",
          clean_df["JourneyId"].nunique())

    print("Number of journey-level observations:",
          len(journey_df))

    print("\nJourneys by product:")
    print(journey_df["Product"].value_counts())

    print("\nObserved journey cost summary by product:")
    print(
        journey_df.groupby("Product")["ObservedJourneyCost"]
        .describe()
    )

    # ========================================

    # Step 7: Identify Monthly Pass Additional Charges
    # This analysis identifies journeys where additional fare charges occurred
    # while using a 1 Zone or 2 Zone Monthly Pass.

    pass_additional_charges = (
        journey_df[
            journey_df["Product"].isin([
                "1 Zone Monthly Pass",
                "2 Zone Monthly Pass"
            ])
            & (journey_df["ObservedJourneyCost"] > 0)
        ]
        .sort_values("JourneyStart")
    )

    print("=== Monthly Pass Journeys with Additional Charges ===")

    display(
        pass_additional_charges[
            [
                "JourneyStart",
                "JourneyEnd",
                "Product",
                "ObservedJourneyCost",
                "JourneyId"
            ]
        ]
    )

    # Specifically identify the $1.75 charge under the 2 Zone Monthly Pass
    print("\n=== 2 Zone Monthly Pass: $1.75 Additional Charge ===")

    display(
        journey_df[
            (journey_df["Product"] == "2 Zone Monthly Pass")
            & (journey_df["ObservedJourneyCost"].round(2) == 1.75)
        ][
            [
                "JourneyStart",
                "JourneyEnd",
                "Product",
                "ObservedJourneyCost",
                "JourneyId"
            ]
        ]
    )

    # Monthly summary of observed journey costs
    print("\n=== Monthly Observed Cost Summary ===")

    monthly_observed_summary = (
        journey_df
        .groupby(["Month", "Product"])
        .agg(
            JourneyCount=("JourneyId", "nunique"),
            ObservedJourneyCost=("ObservedJourneyCost", "sum"),
            MeanJourneyCost=("ObservedJourneyCost", "mean"),
            MedianJourneyCost=("ObservedJourneyCost", "median"),
            MaximumJourneyCost=("ObservedJourneyCost", "max")
        )
        .reset_index()
    )

    display(monthly_observed_summary)

    # ========================================

    # Step 7.1: Validate the $1.75 Additional Fare
    # Inspect all raw transactions associated with the June 10 journey
    # to identify the origin, destination, transfers, and individual charges.

    target_journey_id = "2026-06-11T00:51:00.0000000Z"

    target_journey = (
        clean_df[
            clean_df["JourneyId"] == target_journey_id
        ]
        [
            [
                "DateTime",
                "Transaction",
                "Product",
                "Amount",
                "BalanceDetails",
                "LocationDisplay",
                "JourneyId"
            ]
        ]
        .sort_values("DateTime")
    )

    display(target_journey)

    print("\n=== Journey-Level Summary ===")
    print("Journey Start:", target_journey["DateTime"].min())
    print("Journey End:", target_journey["DateTime"].max())
    print("Product:", target_journey["Product"].iloc[0])
    print("Net Amount:", target_journey["Amount"].sum())
    print("Observed Journey Cost:", -target_journey["Amount"].sum())

    # ========================================

    # Step 8: Monthly Total Expenditure Analysis
    # Calculates actual monthly transit expenditure using:
    # 1. Observed Stored Value journey costs
    # 2. Official Monthly Pass prices
    # 3. Observed additional charges incurred while holding a Monthly Pass


    # Official Monthly Pass prices applicable to the observed pass months
    pass_cost_lookup = {
        "2026-06": 149.25,  # 2 Zone Monthly Pass, pre-July fare
        "2026-07": 156.70,  # 2 Zone Monthly Pass, post-July fare
        "2026-09": 117.20,  # 1 Zone Monthly Pass, post-July fare
        "2026-10": 117.20   # 1 Zone Monthly Pass, post-July fare
    }


    # Aggregate observed journey-level expenditure by month
    monthly_expenditure = (
        journey_df
        .groupby("Month")
        .agg(
            JourneyCount=("JourneyId", "nunique"),
            ObservedJourneyCost=("ObservedJourneyCost", "sum")
        )
        .reset_index()
    )


    # Identify the fare product used in each month
    monthly_product = (
        journey_df
        .groupby("Month")["Product"]
        .agg(lambda x: x.mode().iloc[0])
        .reset_index()
    )

    monthly_expenditure = monthly_expenditure.merge(
        monthly_product,
        on="Month",
        how="left"
    )


    # Add Monthly Pass purchase cost
    monthly_expenditure["MonthlyPassCost"] = (
        monthly_expenditure["Month"]
        .astype(str)
        .map(pass_cost_lookup)
        .fillna(0)
    )


    # Separate observed Stored Value fares from
    # additional charges incurred while using a Monthly Pass
    monthly_expenditure["StoredValueCost"] = monthly_expenditure.apply(
        lambda row:
            row["ObservedJourneyCost"]
            if row["Product"] == "Stored Value"
            else 0,
        axis=1
    )

    monthly_expenditure["AdditionalPassCharges"] = monthly_expenditure.apply(
        lambda row:
            row["ObservedJourneyCost"]
            if "Monthly Pass" in row["Product"]
            else 0,
        axis=1
    )


    # Calculate total monthly expenditure
    monthly_expenditure["TotalExpenditure"] = (
        monthly_expenditure["StoredValueCost"]
        + monthly_expenditure["MonthlyPassCost"]
        + monthly_expenditure["AdditionalPassCharges"]
    )


    # Round monetary variables
    money_columns = [
        "StoredValueCost",
        "MonthlyPassCost",
        "AdditionalPassCharges",
        "TotalExpenditure"
    ]

    monthly_expenditure[money_columns] = (
        monthly_expenditure[money_columns].round(2)
    )


    # Final monthly expenditure table
    monthly_expenditure = monthly_expenditure[
        [
            "Month",
            "Product",
            "JourneyCount",
            "StoredValueCost",
            "MonthlyPassCost",
            "AdditionalPassCharges",
            "TotalExpenditure"
        ]
    ]


    print("=== Monthly Total Expenditure ===")
    display(monthly_expenditure)


    # Overall expenditure during the analysis period
    total_expenditure = monthly_expenditure["TotalExpenditure"].sum()

    print(
        f"\nTotal expenditure during analysis period: "
        f"${total_expenditure:.2f}"
    )

    # ========================================

    # Step 9: Scenario-Based Cost-Effectiveness Analysis
    # Compares the actual Monthly Pass expenditure with hypothetical
    # Stored Value expenditure under 1-Zone, 2-Zone, and 3-Zone scenarios.
    #
    # Important methodological limitation:
    # These are counterfactual scenarios, not exact reconstructed fares.
    # Each scenario assumes that every journey in a given month would have
    # been charged at the same zone level.
    #
    # Positive estimated savings mean the Monthly Pass was cheaper.
    # Negative estimated savings mean Stored Value would have been cheaper.

    import numpy as np


    # --------------------------------------------------
    # 1. Stored Value fare reference by fare period
    # --------------------------------------------------

    stored_value_fares = {
        "Pre-increase": {
            "1_zone": 2.70,
            "2_zone": 4.00,
            "3_zone": 5.10
        },
        "Post-increase": {
            "1_zone": 2.85,
            "2_zone": 4.20,
            "3_zone": 5.40
        }
    }


    # --------------------------------------------------
    # 2. Keep Monthly Pass months only
    # --------------------------------------------------

    cost_effectiveness = monthly_expenditure[
        monthly_expenditure["Product"].isin([
            "1 Zone Monthly Pass",
            "2 Zone Monthly Pass"
        ])
    ].copy()


    # --------------------------------------------------
    # 3. Classify each month by fare period
    # --------------------------------------------------

    cost_effectiveness["FarePeriod"] = np.where(
        cost_effectiveness["Month"].astype(str) < "2026-07",
        "Pre-increase",
        "Post-increase"
    )


    # --------------------------------------------------
    # 4. Assign Stored Value fares applicable to each month
    # --------------------------------------------------

    cost_effectiveness["StoredValue1ZoneFare"] = (
        cost_effectiveness["FarePeriod"]
        .map({
            "Pre-increase": stored_value_fares["Pre-increase"]["1_zone"],
            "Post-increase": stored_value_fares["Post-increase"]["1_zone"]
        })
    )

    cost_effectiveness["StoredValue2ZoneFare"] = (
        cost_effectiveness["FarePeriod"]
        .map({
            "Pre-increase": stored_value_fares["Pre-increase"]["2_zone"],
            "Post-increase": stored_value_fares["Post-increase"]["2_zone"]
        })
    )

    cost_effectiveness["StoredValue3ZoneFare"] = (
        cost_effectiveness["FarePeriod"]
        .map({
            "Pre-increase": stored_value_fares["Pre-increase"]["3_zone"],
            "Post-increase": stored_value_fares["Post-increase"]["3_zone"]
        })
    )


    # --------------------------------------------------
    # 5. Calculate hypothetical Stored Value expenditure
    # --------------------------------------------------

    cost_effectiveness["EstimatedStoredValue1Zone"] = (
        cost_effectiveness["JourneyCount"]
        * cost_effectiveness["StoredValue1ZoneFare"]
    )

    cost_effectiveness["EstimatedStoredValue2Zone"] = (
        cost_effectiveness["JourneyCount"]
        * cost_effectiveness["StoredValue2ZoneFare"]
    )

    cost_effectiveness["EstimatedStoredValue3Zone"] = (
        cost_effectiveness["JourneyCount"]
        * cost_effectiveness["StoredValue3ZoneFare"]
    )


    # --------------------------------------------------
    # 6. Calculate estimated savings
    #
    # Savings = Counterfactual Stored Value Cost
    #           - Actual Monthly Pass Cost
    #
    # Positive value: Monthly Pass was cheaper
    # Negative value: Stored Value was cheaper
    # --------------------------------------------------

    cost_effectiveness["SavingsIf1Zone"] = (
        cost_effectiveness["EstimatedStoredValue1Zone"]
        - cost_effectiveness["TotalExpenditure"]
    )

    cost_effectiveness["SavingsIf2Zone"] = (
        cost_effectiveness["EstimatedStoredValue2Zone"]
        - cost_effectiveness["TotalExpenditure"]
    )

    cost_effectiveness["SavingsIf3Zone"] = (
        cost_effectiveness["EstimatedStoredValue3Zone"]
        - cost_effectiveness["TotalExpenditure"]
    )


    # --------------------------------------------------
    # 7. Calculate break-even journey counts
    #
    # Break-even count:
    # The minimum number of Stored Value journeys at which
    # the actual Monthly Pass expenditure becomes cheaper.
    # --------------------------------------------------

    cost_effectiveness["BreakEven1ZoneJourneys"] = np.ceil(
        cost_effectiveness["TotalExpenditure"]
        / cost_effectiveness["StoredValue1ZoneFare"]
    )

    cost_effectiveness["BreakEven2ZoneJourneys"] = np.ceil(
        cost_effectiveness["TotalExpenditure"]
        / cost_effectiveness["StoredValue2ZoneFare"]
    )

    cost_effectiveness["BreakEven3ZoneJourneys"] = np.ceil(
        cost_effectiveness["TotalExpenditure"]
        / cost_effectiveness["StoredValue3ZoneFare"]
    )


    # --------------------------------------------------
    # 8. Determine cost-effectiveness under each scenario
    # --------------------------------------------------

    cost_effectiveness["ResultIf1Zone"] = np.where(
        cost_effectiveness["SavingsIf1Zone"] > 0,
        "Monthly Pass was cheaper",
        np.where(
            cost_effectiveness["SavingsIf1Zone"] < 0,
            "Stored Value was cheaper",
            "Equal cost"
        )
    )

    cost_effectiveness["ResultIf2Zone"] = np.where(
        cost_effectiveness["SavingsIf2Zone"] > 0,
        "Monthly Pass was cheaper",
        np.where(
            cost_effectiveness["SavingsIf2Zone"] < 0,
            "Stored Value was cheaper",
            "Equal cost"
        )
    )

    cost_effectiveness["ResultIf3Zone"] = np.where(
        cost_effectiveness["SavingsIf3Zone"] > 0,
        "Monthly Pass was cheaper",
        np.where(
            cost_effectiveness["SavingsIf3Zone"] < 0,
            "Stored Value was cheaper",
            "Equal cost"
        )
    )


    # --------------------------------------------------
    # 9. Round monetary variables
    # --------------------------------------------------

    cost_columns = [
        "MonthlyPassCost",
        "AdditionalPassCharges",
        "TotalExpenditure",
        "EstimatedStoredValue1Zone",
        "EstimatedStoredValue2Zone",
        "EstimatedStoredValue3Zone",
        "SavingsIf1Zone",
        "SavingsIf2Zone",
        "SavingsIf3Zone"
    ]

    cost_effectiveness[cost_columns] = (
        cost_effectiveness[cost_columns].round(2)
    )


    # --------------------------------------------------
    # 10. Display the cost comparison
    # --------------------------------------------------

    comparison_columns = [
        "Month",
        "Product",
        "JourneyCount",
        "MonthlyPassCost",
        "AdditionalPassCharges",
        "TotalExpenditure",
        "EstimatedStoredValue1Zone",
        "EstimatedStoredValue2Zone",
        "EstimatedStoredValue3Zone",
        "SavingsIf1Zone",
        "SavingsIf2Zone",
        "SavingsIf3Zone"
    ]

    print("=== Monthly Pass Cost-Effectiveness Analysis ===")

    display(
        cost_effectiveness[comparison_columns]
        .reset_index(drop=True)
    )


    # --------------------------------------------------
    # 11. Display break-even analysis
    # --------------------------------------------------

    break_even_columns = [
        "Month",
        "Product",
        "JourneyCount",
        "BreakEven1ZoneJourneys",
        "BreakEven2ZoneJourneys",
        "BreakEven3ZoneJourneys",
        "ResultIf1Zone",
        "ResultIf2Zone",
        "ResultIf3Zone"
    ]

    print("\n=== Break-Even Analysis ===")

    display(
        cost_effectiveness[break_even_columns]
        .reset_index(drop=True)
    )


    # --------------------------------------------------
    # 12. Overall scenario comparison
    # --------------------------------------------------

    overall_summary = pd.DataFrame({
        "Scenario": [
            "Actual Monthly Pass Expenditure",
            "Stored Value: All 1-Zone",
            "Stored Value: All 2-Zone",
            "Stored Value: All 3-Zone"
        ],
        "TotalCost": [
            cost_effectiveness["TotalExpenditure"].sum(),
            cost_effectiveness["EstimatedStoredValue1Zone"].sum(),
            cost_effectiveness["EstimatedStoredValue2Zone"].sum(),
            cost_effectiveness["EstimatedStoredValue3Zone"].sum()
        ]
    })

    overall_summary["TotalCost"] = (
        overall_summary["TotalCost"].round(2)
    )

    actual_pass_total = (
        cost_effectiveness["TotalExpenditure"].sum()
    )

    overall_summary["DifferenceFromActualPass"] = (
        overall_summary["TotalCost"] - actual_pass_total
    ).round(2)


    print("\n=== Overall Cost Comparison for Monthly Pass Months ===")

    display(overall_summary)

    # ========================================

    # Step 9: Descriptive Analysis
    # Summarizes actual observed spending and travel behaviour.
    # This analysis uses observed Compass Card data only and does not
    # assume hypothetical 1-Zone, 2-Zone, or 3-Zone travel scenarios.

    # -----------------------------------------
    # 1. Overall expenditure statistics
    # -----------------------------------------

    total_expenditure = monthly_expenditure["TotalExpenditure"].sum()
    average_monthly_expenditure = monthly_expenditure["TotalExpenditure"].mean()
    median_monthly_expenditure = monthly_expenditure["TotalExpenditure"].median()

    total_journeys = journey_df["JourneyId"].nunique()
    average_monthly_journeys = monthly_expenditure["JourneyCount"].mean()

    effective_cost_per_journey = total_expenditure / total_journeys


    print("=== Overall Descriptive Statistics ===")

    print(f"Total Expenditure: ${total_expenditure:.2f}")
    print(f"Average Monthly Expenditure: ${average_monthly_expenditure:.2f}")
    print(f"Median Monthly Expenditure: ${median_monthly_expenditure:.2f}")
    print(f"Total Journeys: {total_journeys}")
    print(f"Average Monthly Journeys: {average_monthly_journeys:.1f}")
    print(f"Overall Effective Cost per Journey: ${effective_cost_per_journey:.2f}")


    # -----------------------------------------
    # 2. Monthly effective cost per journey
    # -----------------------------------------

    monthly_analysis = monthly_expenditure.copy()

    monthly_analysis["EffectiveCostPerJourney"] = (
        monthly_analysis["TotalExpenditure"]
        / monthly_analysis["JourneyCount"]
    )

    monthly_analysis["EffectiveCostPerJourney"] = (
        monthly_analysis["EffectiveCostPerJourney"].round(2)
    )


    # -----------------------------------------
    # 3. Display monthly descriptive analysis
    # -----------------------------------------

    print("\n=== Monthly Descriptive Analysis ===")

    display(
        monthly_analysis[
            [
                "Month",
                "Product",
                "JourneyCount",
                "TotalExpenditure",
                "EffectiveCostPerJourney"
            ]
        ]
    )


    # -----------------------------------------
    # 4. Descriptive statistics by fare product
    # -----------------------------------------

    fare_product_summary = (
        monthly_analysis
        .groupby("Product")
        .agg(
            NumberOfMonths=("Month", "count"),
            TotalJourneys=("JourneyCount", "sum"),
            MeanJourneysPerMonth=("JourneyCount", "mean"),
            TotalExpenditure=("TotalExpenditure", "sum"),
            MeanMonthlyExpenditure=("TotalExpenditure", "mean")
        )
        .reset_index()
    )

    fare_product_summary[
        [
            "MeanJourneysPerMonth",
            "TotalExpenditure",
            "MeanMonthlyExpenditure"
        ]
    ] = (
        fare_product_summary[
            [
                "MeanJourneysPerMonth",
                "TotalExpenditure",
                "MeanMonthlyExpenditure"
            ]
        ].round(2)
    )

    print("\n=== Descriptive Statistics by Fare Product ===")

    display(fare_product_summary)

    # ========================================

    # Step 9: Descriptive Analysis
    # Summarizes actual observed spending and travel behaviour.
    # This analysis uses observed Compass Card data only and does not
    # assume hypothetical 1-Zone, 2-Zone, or 3-Zone travel scenarios.

    # -----------------------------------------
    # 1. Overall expenditure statistics
    # -----------------------------------------

    total_expenditure = monthly_expenditure["TotalExpenditure"].sum()
    average_monthly_expenditure = monthly_expenditure["TotalExpenditure"].mean()
    median_monthly_expenditure = monthly_expenditure["TotalExpenditure"].median()

    total_journeys = journey_df["JourneyId"].nunique()
    average_monthly_journeys = monthly_expenditure["JourneyCount"].mean()

    effective_cost_per_journey = total_expenditure / total_journeys


    print("=== Overall Descriptive Statistics ===")

    print(f"Total Expenditure: ${total_expenditure:.2f}")
    print(f"Average Monthly Expenditure: ${average_monthly_expenditure:.2f}")
    print(f"Median Monthly Expenditure: ${median_monthly_expenditure:.2f}")
    print(f"Total Journeys: {total_journeys}")
    print(f"Average Monthly Journeys: {average_monthly_journeys:.1f}")
    print(f"Overall Effective Cost per Journey: ${effective_cost_per_journey:.2f}")


    # -----------------------------------------
    # 2. Monthly effective cost per journey
    # -----------------------------------------

    monthly_analysis = monthly_expenditure.copy()

    monthly_analysis["EffectiveCostPerJourney"] = (
        monthly_analysis["TotalExpenditure"]
        / monthly_analysis["JourneyCount"]
    )

    monthly_analysis["EffectiveCostPerJourney"] = (
        monthly_analysis["EffectiveCostPerJourney"].round(2)
    )


    # -----------------------------------------
    # 3. Display monthly descriptive analysis
    # -----------------------------------------

    print("\n=== Monthly Descriptive Analysis ===")

    display(
        monthly_analysis[
            [
                "Month",
                "Product",
                "JourneyCount",
                "TotalExpenditure",
                "EffectiveCostPerJourney"
            ]
        ]
    )


    # -----------------------------------------
    # 4. Descriptive statistics by fare product
    # -----------------------------------------

    fare_product_summary = (
        monthly_analysis
        .groupby("Product")
        .agg(
            NumberOfMonths=("Month", "count"),
            TotalJourneys=("JourneyCount", "sum"),
            MeanJourneysPerMonth=("JourneyCount", "mean"),
            TotalExpenditure=("TotalExpenditure", "sum"),
            MeanMonthlyExpenditure=("TotalExpenditure", "mean")
        )
        .reset_index()
    )

    fare_product_summary[
        [
            "MeanJourneysPerMonth",
            "TotalExpenditure",
            "MeanMonthlyExpenditure"
        ]
    ] = (
        fare_product_summary[
            [
                "MeanJourneysPerMonth",
                "TotalExpenditure",
                "MeanMonthlyExpenditure"
            ]
        ].round(2)
    )

    print("\n=== Descriptive Statistics by Fare Product ===")

    display(fare_product_summary)

    # ========================================

    # Step 10: Data Visualization
    # Visualizes monthly expenditure, journey frequency,
    # and effective average cost per journey.

    import matplotlib.pyplot as plt

    # Create plotting dataset
    plot_df = monthly_analysis.copy()
    plot_df["MonthLabel"] = plot_df["Month"].astype(str)


    # 1. Monthly Total Expenditure

    plt.figure(figsize=(10, 5))

    plt.bar(
        plot_df["MonthLabel"],
        plot_df["TotalExpenditure"]
    )

    plt.title("Monthly Transit Expenditure")
    plt.xlabel("Month")
    plt.ylabel("Expenditure (CAD)")
    plt.xticks(rotation=45)

    plt.tight_layout()
    plt.show()


    # 2. Monthly Journey Frequency

    plt.figure(figsize=(10, 5))

    plt.bar(
        plot_df["MonthLabel"],
        plot_df["JourneyCount"]
    )

    plt.title("Monthly Journey Frequency")
    plt.xlabel("Month")
    plt.ylabel("Number of Journeys")
    plt.xticks(rotation=45)

    plt.tight_layout()
    plt.show()


    # 3. Effective Average Cost per Journey

    plt.figure(figsize=(10, 5))

    plt.plot(
        plot_df["MonthLabel"],
        plot_df["EffectiveCostPerJourney"],
        marker="o"
    )

    plt.title("Effective Average Cost per Journey")
    plt.xlabel("Month")
    plt.ylabel("Average Cost per Journey (CAD)")
    plt.xticks(rotation=45)

    plt.tight_layout()
    plt.show()

    # ========================================

    # Step 11: Observed Cost-Effectiveness Analysis
    # Evaluates fare-product efficiency using actual observed expenditure
    # and actual journey frequency only.
    #
    # Key metric:
    # Effective Average Cost per Journey =
    # Total Monthly Expenditure / Number of Journeys

    # Create analysis dataset
    cost_efficiency = monthly_analysis.copy()


    # Calculate effective average cost per journey
    cost_efficiency["EffectiveAverageCostPerJourney"] = (
        cost_efficiency["TotalExpenditure"]
        / cost_efficiency["JourneyCount"]
    ).round(2)


    # Summarize by fare product
    fare_efficiency_summary = (
        cost_efficiency
        .groupby("Product")
        .agg(
            MonthsObserved=("Month", "count"),
            TotalJourneys=("JourneyCount", "sum"),
            AverageJourneysPerMonth=("JourneyCount", "mean"),
            TotalExpenditure=("TotalExpenditure", "sum"),
            AverageMonthlyExpenditure=("TotalExpenditure", "mean")
        )
        .reset_index()
    )


    # Calculate overall effective average cost per journey
    fare_efficiency_summary["EffectiveAverageCostPerJourney"] = (
        fare_efficiency_summary["TotalExpenditure"]
        / fare_efficiency_summary["TotalJourneys"]
    )


    # Round numeric results
    columns_to_round = [
        "AverageJourneysPerMonth",
        "TotalExpenditure",
        "AverageMonthlyExpenditure",
        "EffectiveAverageCostPerJourney"
    ]

    fare_efficiency_summary[columns_to_round] = (
        fare_efficiency_summary[columns_to_round].round(2)
    )


    # Display monthly results
    print("=== Monthly Observed Cost Efficiency ===")

    display(
        cost_efficiency[
            [
                "Month",
                "Product",
                "JourneyCount",
                "TotalExpenditure",
                "EffectiveAverageCostPerJourney"
            ]
        ]
    )


    # Display fare-product comparison
    print("\n=== Fare Product Cost Efficiency ===")

    display(fare_efficiency_summary)


    # Identify the most cost-efficient observed month
    most_efficient_month = cost_efficiency.loc[
        cost_efficiency["EffectiveAverageCostPerJourney"].idxmin()
    ]

    print("\n=== Most Cost-Efficient Observed Month ===")

    print("Month:", most_efficient_month["Month"])
    print("Fare Product:", most_efficient_month["Product"])
    print("Journeys:", most_efficient_month["JourneyCount"])
    print(
        "Effective Average Cost per Journey:",
        f'${most_efficient_month["EffectiveAverageCostPerJourney"]:.2f}'
    )

    # ========================================

    # Step 12: Findings and Interpretation
    # Summarizes the main empirical findings from the Compass Card analysis.
    # The interpretation is based on observed expenditure and travel behaviour.
    # It does not claim that one fare product is universally more cost-effective.

    # --------------------------------------------------
    # 1. Extract key statistics
    # --------------------------------------------------

    total_expenditure = monthly_expenditure["TotalExpenditure"].sum()
    total_journeys = journey_df["JourneyId"].nunique()

    average_monthly_expenditure = (
        monthly_expenditure["TotalExpenditure"].mean()
    )

    median_monthly_expenditure = (
        monthly_expenditure["TotalExpenditure"].median()
    )

    overall_effective_cost = (
        total_expenditure / total_journeys
    )


    # --------------------------------------------------
    # 2. Identify highest and lowest expenditure months
    # --------------------------------------------------

    highest_spending_month = monthly_expenditure.loc[
        monthly_expenditure["TotalExpenditure"].idxmax()
    ]

    lowest_spending_month = monthly_expenditure.loc[
        monthly_expenditure["TotalExpenditure"].idxmin()
    ]


    # --------------------------------------------------
    # 3. Identify highest-usage and most efficient months
    # --------------------------------------------------

    highest_usage_month = cost_efficiency.loc[
        cost_efficiency["JourneyCount"].idxmax()
    ]

    most_efficient_month = cost_efficiency.loc[
        cost_efficiency["EffectiveAverageCostPerJourney"].idxmin()
    ]


    # --------------------------------------------------
    # 4. Display Key Findings
    # --------------------------------------------------

    print("=== Key Findings ===")

    print(
        f"Analysis Period: "
        f"{clean_df['DateTime'].min().date()} to "
        f"{clean_df['DateTime'].max().date()}"
    )

    print(f"Total Expenditure: ${total_expenditure:.2f}")
    print(f"Total Journeys: {total_journeys}")

    print(
        f"Average Monthly Expenditure: "
        f"${average_monthly_expenditure:.2f}"
    )

    print(
        f"Median Monthly Expenditure: "
        f"${median_monthly_expenditure:.2f}"
    )

    print(
        f"Overall Effective Average Cost per Journey: "
        f"${overall_effective_cost:.2f}"
    )


    # --------------------------------------------------
    # 5. Monthly extrema
    # --------------------------------------------------

    print("\n=== Monthly Highlights ===")

    print(
        f"Highest Spending Month: "
        f"{highest_spending_month['Month']} | "
        f"${highest_spending_month['TotalExpenditure']:.2f} | "
        f"{highest_spending_month['Product']}"
    )

    print(
        f"Lowest Spending Month: "
        f"{lowest_spending_month['Month']} | "
        f"${lowest_spending_month['TotalExpenditure']:.2f} | "
        f"{lowest_spending_month['Product']}"
    )

    print(
        f"Highest Journey Frequency: "
        f"{highest_usage_month['Month']} | "
        f"{highest_usage_month['JourneyCount']} journeys"
    )

    print(
        f"Lowest Effective Average Cost per Journey: "
        f"{most_efficient_month['Month']} | "
        f"${most_efficient_month['EffectiveAverageCostPerJourney']:.2f}"
    )


    # --------------------------------------------------
    # 6. Fare-product-level findings
    # --------------------------------------------------

    print("\n=== Fare Product Comparison ===")

    display(fare_efficiency_summary)


    # --------------------------------------------------
    # 7. Interpretation
    # --------------------------------------------------

    print("\n=== Interpretation ===")

    print(
        "Monthly Pass months were associated with substantially higher "
        "journey frequency than Stored Value months."
    )

    print(
        "The observed effective average cost per journey decreased as "
        "journey frequency increased during Monthly Pass months."
    )

    print(
        "Among the observed fare-product periods, the 1 Zone Monthly Pass "
        "had the lowest effective average cost per journey."
    )

    print(
        "This should be interpreted as an observational association rather "
        "than evidence that a 1 Zone Monthly Pass is always the cheapest option."
    )


    # --------------------------------------------------
    # 8. Limitations
    # --------------------------------------------------

    print("\n=== Limitations ===")

    print(
        "1. February begins on February 9, and November ends on November 20, "
        "so these are partial months."
    )

    print(
        "2. Monthly Pass purchase prices were not recorded directly in the "
        "Compass Card export and were incorporated from the applicable "
        "TransLink fare schedule."
    )

    print(
        "3. Additional Monthly Pass charges were included when they were "
        "observed in the transaction history."
    )

    print(
        "4. The current analysis does not reconstruct a hypothetical Stored "
        "Value fare for every Monthly Pass journey."
    )

    print(
        "5. Therefore, the analysis describes observed cost efficiency but "
        "does not establish the counterfactual savings from choosing one fare "
        "product instead of another."
    )


    # --------------------------------------------------
    # 9. Conclusion
    # --------------------------------------------------

    print("\n=== Conclusion ===")

    print(
        f"From February 9 to November 20, 2026, a total of "
        f"{total_journeys} journeys were observed, with total estimated "
        f"transit expenditure of ${total_expenditure:.2f}."
    )

    print(
        f"The overall effective average cost was "
        f"${overall_effective_cost:.2f} per journey."
    )

    print(
        f"The most cost-efficient observed month was "
        f"{most_efficient_month['Month']}, when "
        f"{most_efficient_month['Product']} was used for "
        f"{most_efficient_month['JourneyCount']} journeys, resulting in an "
        f"effective average cost of "
        f"${most_efficient_month['EffectiveAverageCostPerJourney']:.2f} "
        f"per journey."
    )

    print(
        "Overall, the observed data suggest that Monthly Passes were associated "
        "with greater cost efficiency during high-frequency travel months, "
        "while Stored Value was predominantly used during lower-frequency "
        "travel months."
    )

    # ========================================

    # Check the current working directory and files

    import os
    from pathlib import Path

    print("Current working directory:")
    print(os.getcwd())

    print("\nFiles in this directory:")
    for file in os.listdir():
        print(file)

    print("\nFull file paths:")
    for file in os.listdir():
        print(Path(file).resolve())

    # ========================================


    return {
        "journeys": journey_df,
        "monthly_expenditure": monthly_expenditure,
        "monthly_analysis": monthly_analysis,
        "fare_efficiency": fare_efficiency_summary,
        "total_expenditure": total_expenditure
    }
