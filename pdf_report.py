# FINTECH_TWO_PAGE_FIX_V2
# FINTECH_TWO_PAGE_V1
# FINTECH_SPACING_V1
from io import BytesIO
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet



# FINTECH_PDF_STYLE_V1

# FINTECH_CHART_STYLE_V1

# FINTECH_LAYOUT_V1
def draw_fintech_footer(canvas, doc):
    from reportlab.lib import colors

    canvas.saveState()

    width, _ = doc.pagesize

    canvas.setStrokeColor(colors.HexColor("#E2E8F0"))
    canvas.setLineWidth(0.5)
    canvas.line(48, 42, width - 48, 42)

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#64748B"))

    canvas.drawString(
        48, 28,
        "COMPASS CARD | FARE ANALYSIS"
    )

    canvas.drawRightString(
        width - 48, 28,
        f"PAGE {doc.page}"
    )

    canvas.restoreState()

def style_fintech_chart(ax):
    ax.set_facecolor("#FFFFFF")

    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.grid(
        axis="y",
        color="#E2E8F0",
        linewidth=0.8
    )
    ax.set_axisbelow(True)

    ax.tick_params(
        axis="both",
        colors="#475569",
        labelsize=8,
        length=0
    )

    ax.yaxis.label.set_color("#142B49")
    ax.xaxis.label.set_color("#142B49")

    # Change appearance only; preserve bar heights and positions
    for bar in ax.patches:
        bar.set_facecolor("#2563EB")
        bar.set_edgecolor("none")

def apply_fintech_style(styles):
    from reportlab.lib import colors

    navy = colors.HexColor("#142B49")
    blue = colors.HexColor("#2563EB")
    slate = colors.HexColor("#475569")

    styles["Title"].fontName = "Helvetica-Bold"
    styles["Title"].fontSize = 23
    styles["Title"].leading = 29
    styles["Title"].textColor = navy
    styles["Title"].spaceAfter = 24

    styles["Heading2"].fontName = "Helvetica-Bold"
    styles["Heading2"].fontSize = 13
    styles["Heading2"].leading = 18
    styles["Heading2"].textColor = blue
    styles["Heading2"].spaceBefore = 18
    styles["Heading2"].spaceAfter = 12

    styles["Normal"].fontName = "Helvetica"
    styles["Normal"].fontSize = 9
    styles["Normal"].leading = 15
    styles["Normal"].textColor = slate

    return styles

def generate_pdf(results):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        leftMargin=48,
        rightMargin=48,
        topMargin=48,
        bottomMargin=48
    )
    styles = apply_fintech_style(getSampleStyleSheet())
    styles["Heading2"].keepWithNext = True

    elements = []

    journeys = results["journeys"]
    total = results["total_expenditure"]

    elements.append(
        Paragraph("Compass Card Fare Analysis Report", styles["Title"])
    )
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Overview", styles["Heading2"]))

    overview = [
        ["Metric", "Value"],
        ["Total Journeys", str(len(journeys))],
        ["Total Expenditure", f"${total:.2f}"],
        [
            "Average Cost per Journey",
            f"${total / len(journeys):.2f}" if len(journeys) else "N/A"
        ],
    ]

    # FINTECH_TABLE_STYLE_V1
    from reportlab.lib import colors as fc

    navy = fc.HexColor("#142B49")
    blue = fc.HexColor("#2563EB")
    pale_blue = fc.HexColor("#EFF6FF")
    border = fc.HexColor("#E2E8F0")

    # KPI summary card
    kpi = Table(overview, colWidths=[280, 170])
    kpi.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), navy),
        ("TEXTCOLOR", (0, 0), (-1, 0), fc.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 1), (-1, -1), pale_blue),
        ("TEXTCOLOR", (0, 1), (-1, -1), navy),
        ("FONTNAME", (1, 1), (1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (1, 1), (1, -1), 12),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("LINEBELOW", (0, 0), (-1, 0), 1, blue),
        ("LINEBELOW", (0, 1), (-1, -2), 0.5, border),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
    ]))
    elements.append(kpi)
    elements.append(Spacer(1, 10))

    elements.append(
        Paragraph("Monthly Expenditure", styles["Heading2"])
    )

    monthly = results["monthly_expenditure"]

    data = [["Month", "Product", "Journeys", "Total (CAD)"]]

    for _, row in monthly.iterrows():
        data.append([
            str(row["Month"]),
            str(row["Product"]),
            str(row["JourneyCount"]),
            f'${row["TotalExpenditure"]:.2f}',
        ])

    table = Table(data, repeatRows=1)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), navy),
        ("TEXTCOLOR", (0, 0), (-1, 0), fc.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [fc.white, pale_blue]),
        ("TEXTCOLOR", (0, 1), (-1, -1), navy),
        ("LINEBELOW", (0, 0), (-1, 0), 1, blue),
        ("LINEBELOW", (0, 1), (-1, -1), 0.3, border),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))

    elements.append(table)

    # FINTECH_PAGE_LAYOUT_V2
    from reportlab.platypus import PageBreak

    # Page 2: Spending and journey frequency
    elements.append(PageBreak())

    # Monthly spending chart
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from reportlab.platypus import Image

    fig, ax = plt.subplots(figsize=(8, 2.5))
    ax.bar(
        monthly["Month"].astype(str),
        monthly["TotalExpenditure"]
    )
    ax.set_ylabel("Expenditure (CAD)")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()

    chart_buffer = BytesIO()
    style_fintech_chart(ax)
    fig.savefig(chart_buffer, format="png", dpi=150)
    plt.close(fig)
    chart_buffer.seek(0)

    elements.append(Spacer(1, 10))
    elements.append(
        Paragraph("Monthly Spending Chart", styles["Heading2"])
    )
    elements.append(Image(chart_buffer, width=460, height=125))

    # Monthly journey frequency chart
    fig, ax = plt.subplots(figsize=(8, 2.5))
    ax.bar(
        monthly["Month"].astype(str),
        monthly["JourneyCount"]
    )
    ax.set_ylabel("Number of Journeys")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()

    frequency_buffer = BytesIO()
    style_fintech_chart(ax)
    fig.savefig(frequency_buffer, format="png", dpi=150)
    plt.close(fig)
    frequency_buffer.seek(0)

    elements.append(Spacer(1, 10))
    elements.append(
        Paragraph("Monthly Journey Frequency", styles["Heading2"])
    )
    elements.append(
        Image(frequency_buffer, width=460, height=125)
    )

    # Average cost per journey chart
    cost_chart = monthly.copy()
    cost_chart["CostPerJourney"] = (
        cost_chart["TotalExpenditure"]
        / cost_chart["JourneyCount"].replace(0, float("nan"))
    )

    # Removed page break for two-page layout

    fig, ax = plt.subplots(figsize=(8, 2.5))
    ax.bar(
        cost_chart["Month"].astype(str),
        cost_chart["CostPerJourney"]
    )
    ax.set_ylabel("Average Cost per Journey (CAD)")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()

    cost_buffer = BytesIO()
    style_fintech_chart(ax)
    fig.savefig(cost_buffer, format="png", dpi=150)
    plt.close(fig)
    cost_buffer.seek(0)

    elements.append(Spacer(1, 10))
    elements.append(
        Paragraph("Cost per Journey by Month", styles["Heading2"])
    )
    elements.append(
        Image(cost_buffer, width=460, height=125)
    )

    elements.append(Spacer(1, 10))
    elements.append(
        Paragraph("Interpretation and Limitations", styles["Heading2"])
    )

    notes = [
        "Average cost per journey reflects observed expenditure.",
        "Monthly Pass costs are calculated using versioned TransLink fare reference data, with rates applied according to their effective dates.",
        "Partial months may not be directly comparable to full months.",
        "This report does not estimate hypothetical Stored Value costs for Monthly Pass journeys.",
    ]

    for note in notes:
        elements.append(Paragraph("- " + note, styles["Normal"]))
        elements.append(Spacer(1, 4))

    doc.build(
        elements,
        onFirstPage=draw_fintech_footer,
        onLaterPages=draw_fintech_footer
    )

    return buffer.getvalue()
