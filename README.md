# Compass Card Fare Analyzer

A privacy-conscious transit spending analytics dashboard built with Python and Streamlit.

This project analyzes exported Compass Card transaction history to help users understand transit spending, journey frequency, and observed fare efficiency.

## Live Demo

**[Launch the Compass Card Fare Analyzer](https://compass-fare-analyzer.streamlit.app/)**

Try the deployed Streamlit dashboard directly in your browser.
No installation or repository cloning is required.

## Features

- Upload and validate Compass Card CSV exports
- Perform data quality checks
- Aggregate transactions into unique journeys
- Analyze monthly transit expenditure and journey frequency
- Calculate effective average cost per journey
- Compare observed Stored Value and Monthly Pass usage
- Apply historical fare rates using a versioned CSV reference
- Visualize transit spending and travel patterns
- Download a two-page PDF analysis report

## Tech Stack

- Python
- pandas and NumPy
- Streamlit
- Matplotlib
- ReportLab

## Project Structure

- app.py — Streamlit dashboard
- analysis.py — CSV validation
- analysis_streamlit.py — Fare analysis
- data_quality.py — Data quality checks
- fare_reference.csv — Historical fare reference
- pdf_report.py — PDF report generation
- requirements.txt — Python dependencies

## Run Locally (For Developers)

1. Clone the repository.
2. Create a Python virtual environment.
3. Install dependencies using: pip install -r requirements.txt
4. Launch the app using: streamlit run app.py
5. Upload your exported Compass Card CSV.

## Methodology and Limitations

- Journey counts are based on unique journey identifiers.
- Monthly expenditure incorporates applicable Monthly Pass prices and observed additional charges.
- Average cost per journey reflects observed expenditure.
- Partial months may not be directly comparable with complete months.
- The analysis does not estimate hypothetical Stored Value costs for Monthly Pass journeys.
- Results do not establish which fare product is universally cheapest.

## Privacy

The deployed application processes uploaded CSV data on Streamlit Community Cloud. Avoid uploading sensitive transaction data unless you are comfortable with cloud-based processing.

Personal Compass Card CSV files are excluded from Git version control through .gitignore.

Review generated reports before sharing them.

## Project Status

Functional local prototype with CSV validation, data quality checks, interactive analytics, historical fare configuration, and PDF reporting.

## Disclaimer

This independent personal project is not affiliated with or endorsed by TransLink.
