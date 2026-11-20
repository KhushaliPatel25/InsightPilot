
from pathlib import Path
import duckdb
import pandas as pd

# --------------------------------------------------
# INSIGHTPILOT - SALES TRENDS & ANOMALY DETECTION
# --------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
DB_FILE = ROOT / "data" / "insightpilot.duckdb"
REPORT_DIR = ROOT / "reports"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

if not DB_FILE.exists():
    raise FileNotFoundError(
        "Database not found. Run 01_build_database.py first."
    )

print("=" * 70)
print("INSIGHTPILOT - SALES TRENDS & ANOMALY DETECTION")
print("=" * 70)

con = duckdb.connect(str(DB_FILE), read_only=True)

try:
    # --------------------------------------------------
    # 1. MONTHLY BUSINESS PERFORMANCE
    # --------------------------------------------------

    monthly_query = """
    WITH monthly_sales AS (
        SELECT
            CAST(
                DATE_TRUNC('month', order_date) AS DATE
            ) AS month,
            COUNT(*) AS total_orders,
            ROUND(SUM(revenue), 2) AS revenue,
            ROUND(SUM(profit), 2) AS profit,
            ROUND(AVG(discount_pct), 2) AS avg_discount_pct
        FROM orders
        GROUP BY 1
    )
    SELECT
        *,
        ROUND(
            100.0 * (
                revenue - LAG(revenue) OVER (ORDER BY month)
            ) / NULLIF(
                LAG(revenue) OVER (ORDER BY month), 0
            ),
            2
        ) AS revenue_growth_pct
    FROM monthly_sales
    ORDER BY month
    """

    monthly_df = con.execute(monthly_query).fetchdf()

    if monthly_df.empty:
        raise ValueError("No monthly sales records found.")

    monthly_df["month"] = pd.to_datetime(
        monthly_df["month"]
    ).dt.strftime("%Y-%m")

    print("\n" + "=" * 70)
    print("MONTHLY SALES PERFORMANCE")
    print("=" * 70)

    print(
        monthly_df[
            [
                "month",
                "total_orders",
                "revenue",
                "profit",
                "revenue_growth_pct",
            ]
        ].to_string(index=False)
    )

    monthly_df.to_csv(
        REPORT_DIR / "04_monthly_sales_trends.csv",
        index=False
    )

    # --------------------------------------------------
    # 2. MONTHLY CATEGORY DISCOUNT ANALYSIS
    # --------------------------------------------------

    discount_query = """
    SELECT
        CAST(
            DATE_TRUNC('month', o.order_date) AS DATE
        ) AS month,
        p.category,
        COUNT(*) AS total_orders,
        ROUND(AVG(o.discount_pct), 2) AS avg_discount_pct,
        ROUND(SUM(o.revenue), 2) AS revenue,
        ROUND(SUM(o.profit), 2) AS profit,
        ROUND(
            100.0 * SUM(o.profit)
            / NULLIF(SUM(o.revenue), 0),
            2
        ) AS profit_margin_pct
    FROM orders o
    JOIN products p
        ON o.product_id = p.product_id
    GROUP BY 1, 2
    ORDER BY 1, 2
    """

    discount_df = con.execute(discount_query).fetchdf()

    discount_df["month"] = pd.to_datetime(
        discount_df["month"]
    ).dt.strftime("%Y-%m")

    discount_df.to_csv(
        REPORT_DIR / "04_category_discount_trends.csv",
        index=False
    )

    # --------------------------------------------------
    # 3. ELECTRONICS DISCOUNT ANOMALY
    # --------------------------------------------------

    electronics = discount_df[
        discount_df["category"] == "Electronics"
    ].copy()

    # Use only months before September 2026
    # to establish the historical baseline.
    baseline = electronics[
        electronics["month"] < "2026-09"
    ]

    if len(baseline) < 6:
        raise ValueError(
            "Insufficient historical months for anomaly detection."
        )

    baseline_mean = baseline["avg_discount_pct"].mean()
    baseline_std = baseline["avg_discount_pct"].std(ddof=1)

    # Statistical alert threshold: mean + 3 standard deviations
    threshold = baseline_mean + (3 * baseline_std)

    electronics["anomaly_score"] = (
        (electronics["avg_discount_pct"] - baseline_mean)
        / baseline_std
        if baseline_std > 0
        else 0.0
    )

    electronics["is_anomaly"] = (
        electronics["avg_discount_pct"] > threshold
    )

    anomalies = electronics[
        electronics["is_anomaly"]
    ].copy()

    target = electronics[
        electronics["month"] == "2026-09"
    ]

    if target.empty:
        raise ValueError(
            "September 2026 Electronics data is missing."
        )

    target_row = target.iloc[0]

    baseline_margin = baseline["profit_margin_pct"].mean()
    target_margin = target_row["profit_margin_pct"]

    # --------------------------------------------------
    # 4. DISPLAY ANOMALY FINDINGS
    # --------------------------------------------------

    print("\n" + "=" * 70)
    print("ELECTRONICS DISCOUNT ANOMALY DETECTION")
    print("=" * 70)

    print(
        f"\nHistorical Average Discount: "
        f"{baseline_mean:.2f}%"
    )

    print(
        f"Historical Standard Deviation: "
        f"{baseline_std:.2f} percentage points"
    )

    print(
        f"Anomaly Alert Threshold: "
        f"{threshold:.2f}%"
    )

    print(
        f"\nSeptember 2026 Average Discount: "
        f"{target_row['avg_discount_pct']:.2f}%"
    )

    print(
        f"September 2026 Anomaly Score: "
        f"{target_row['anomaly_score']:.2f}"
    )

    print(
        f"\nHistorical Average Profit Margin: "
        f"{baseline_margin:.2f}%"
    )

    print(
        f"September 2026 Profit Margin: "
        f"{target_margin:.2f}%"
    )

    print(
        f"Margin Difference: "
        f"{target_margin - baseline_margin:+.2f} "
        f"percentage points"
    )

    print("\n" + "=" * 70)
    print("AUTOMATED ANOMALY FINDINGS")
    print("=" * 70)

    if anomalies.empty:
        print("No discount anomalies detected.")
    else:
        for _, row in anomalies.iterrows():
            print(
                f"\nANOMALY DETECTED: {row['month']}"
            )
            print("Category: Electronics")
            print(
                f"Average Discount: "
                f"{row['avg_discount_pct']:.2f}%"
            )
            print(
                f"Anomaly Score: "
                f"{row['anomaly_score']:.2f}"
            )
            print(
                "Recommendation: Review promotional "
                "pricing and discount approvals."
            )

    # --------------------------------------------------
    # 5. EXPORT ANOMALY RESULTS
    # --------------------------------------------------

    electronics.to_csv(
        REPORT_DIR / "04_electronics_anomaly_scores.csv",
        index=False
    )

    # --------------------------------------------------
    # 6. AUTOMATED MARKDOWN REPORT
    # --------------------------------------------------

    report = [
        "# InsightPilot - Sales Trend & Anomaly Detection",
        "",
        "## Dataset",
        "",
        "Synthetic retail transactions covering "
        "January 2025 to October 2026.",
        "",
        "## Detection Method",
        "",
        "Electronics monthly average discount rates "
        "are compared against historical months "
        "before September 2026.",
        "",
        "An observation is flagged if its average "
        "discount exceeds the historical mean "
        "plus three standard deviations.",
        "",
        "This is a one-sided statistical rule, "
        "not proof of fraud or wrongdoing.",
        "",
        "## Findings",
        "",
        f"- Historical discount: {baseline_mean:.2f}%",
        f"- Alert threshold: {threshold:.2f}%",
        (
            f"- September 2026 discount: "
            f"{target_row['avg_discount_pct']:.2f}%"
        ),
        (
            f"- September anomaly score: "
            f"{target_row['anomaly_score']:.2f}"
        ),
        (
            f"- Historical average monthly margin: "
            f"{baseline_margin:.2f}%"
        ),
        (
            f"- September profit margin: "
            f"{target_margin:.2f}%"
        ),
        "",
        "## Detected Anomalies",
        "",
    ]

    if anomalies.empty:
        report.append("No anomalies detected.")
    else:
        for _, row in anomalies.iterrows():
            report.append(
                f"- {row['month']}: "
                f"{row['avg_discount_pct']:.2f}% "
                f"average discount."
            )

    report.extend([
        "",
        "## Business Recommendation",
        "",
        "Review unusual discount activity, promotional "
        "campaigns, approval controls, and category "
        "profit margins before drawing conclusions.",
        "",
        "The margin comparison is descriptive and "
        "does not establish that discounts alone "
        "caused a margin change.",
        "",
        "## Limitations",
        "",
        "The September 2026 discount anomaly was "
        "intentionally injected into synthetic data. "
        "The historical baseline is selected before "
        "the simulated event, so this is a "
        "demonstration rather than independent "
        "discovery of an unknown anomaly.",
    ])

    (
        REPORT_DIR / "04_discount_anomaly_insights.md"
    ).write_text(
        "\n".join(report) + "\n",
        encoding="utf-8"
    )

    # --------------------------------------------------
    # 7. FINAL VALIDATION
    # --------------------------------------------------

    assert len(monthly_df) == 22
    assert bool(target_row["is_anomaly"])
    assert "2026-09" in anomalies["month"].values

    print("\n" + "=" * 70)
    print("REPORT GENERATION COMPLETE")
    print("=" * 70)

    print("\nFiles created:")
    print("04_monthly_sales_trends.csv")
    print("04_category_discount_trends.csv")
    print("04_electronics_anomaly_scores.csv")
    print("04_discount_anomaly_insights.md")

    print("\nSUCCESS! ANOMALY DETECTION COMPLETE")

finally:
    con.close()
