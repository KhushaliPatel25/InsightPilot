
from pathlib import Path
import duckdb

# --------------------------------------------------
# INSIGHTPILOT - REGIONAL SALES & PROFITABILITY
# --------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
DB_FILE = ROOT / "data" / "insightpilot.duckdb"
REPORT_DIR = ROOT / "reports"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

if not DB_FILE.exists():
    raise FileNotFoundError(
        "Database not found. Run 01_build_database.py first."
    )

print("=" * 72)
print("INSIGHTPILOT - REGIONAL SALES & PROFITABILITY ANALYSIS")
print("=" * 72)

con = duckdb.connect(str(DB_FILE), read_only=True)

try:
    # --------------------------------------------------
    # SQL REGIONAL PERFORMANCE ANALYSIS
    # --------------------------------------------------

    query = """
    WITH regional_metrics AS (
        SELECT
            region,
            COUNT(*) AS total_orders,
            COUNT(DISTINCT customer_id) AS unique_customers,
            SUM(quantity) AS units_sold,
            ROUND(SUM(revenue), 2) AS total_revenue,
            ROUND(SUM(profit), 2) AS total_profit,
            ROUND(AVG(revenue), 2) AS avg_order_value,
            ROUND(
                100.0 * SUM(profit)
                / NULLIF(SUM(revenue), 0),
                2
            ) AS profit_margin_pct
        FROM orders
        GROUP BY region
    )
    SELECT
        *,
        ROUND(
            100.0 * total_revenue
            / NULLIF(SUM(total_revenue) OVER (), 0),
            2
        ) AS revenue_share_pct,
        ROW_NUMBER() OVER (
            ORDER BY total_revenue DESC
        ) AS revenue_rank
    FROM regional_metrics
    ORDER BY revenue_rank
    """

    df = con.execute(query).fetchdf()

    if df.empty:
        raise ValueError("No regional records found.")

    # --------------------------------------------------
    # DISPLAY REGIONAL PERFORMANCE
    # --------------------------------------------------

    print("\nREGIONAL PERFORMANCE SUMMARY\n")

    for _, row in df.iterrows():
        print("-" * 60)
        print(f"Region: {row['region']}")
        print(f"Revenue Rank: {int(row['revenue_rank'])}")
        print(f"Total Orders: {int(row['total_orders']):,}")
        print(
            f"Unique Customers: "
            f"{int(row['unique_customers']):,}"
        )
        print(f"Units Sold: {int(row['units_sold']):,}")
        print(
            f"Total Revenue: "
            f"CAD ${row['total_revenue']:,.2f}"
        )
        print(
            f"Total Profit: "
            f"CAD ${row['total_profit']:,.2f}"
        )
        print(
            f"Average Order Value: "
            f"CAD ${row['avg_order_value']:,.2f}"
        )
        print(
            f"Profit Margin: "
            f"{row['profit_margin_pct']:.2f}%"
        )
        print(
            f"Revenue Share: "
            f"{row['revenue_share_pct']:.2f}%"
        )

    # --------------------------------------------------
    # KEY BUSINESS INSIGHTS
    # --------------------------------------------------

    top_revenue = df.loc[
        df["total_revenue"].idxmax()
    ]

    top_profit = df.loc[
        df["total_profit"].idxmax()
    ]

    top_margin = df.loc[
        df["profit_margin_pct"].idxmax()
    ]

    lowest_margin = df.loc[
        df["profit_margin_pct"].idxmin()
    ]

    total_revenue = df["total_revenue"].sum()
    total_profit = df["total_profit"].sum()

    print("\n" + "=" * 72)
    print("KEY REGIONAL BUSINESS INSIGHTS")
    print("=" * 72)

    print(
        f"\nHighest Revenue Region: "
        f"{top_revenue['region']}"
    )

    print(
        f"Highest Profit Region: "
        f"{top_profit['region']}"
    )

    print(
        f"Highest Profit Margin Region: "
        f"{top_margin['region']} "
        f"({top_margin['profit_margin_pct']:.2f}%)"
    )

    print(
        f"Lowest Profit Margin Region: "
        f"{lowest_margin['region']} "
        f"({lowest_margin['profit_margin_pct']:.2f}%)"
    )

    print(
        f"\nTop Region Revenue Contribution: "
        f"{top_revenue['revenue_share_pct']:.2f}%"
    )

    print(
        f"Total Business Revenue: "
        f"CAD ${total_revenue:,.2f}"
    )

    print(
        f"Total Business Profit: "
        f"CAD ${total_profit:,.2f}"
    )

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    assert len(df) == 5, "Expected five regions."
    assert int(df["total_orders"].sum()) == 15000
    assert abs(
        float(df["revenue_share_pct"].sum()) - 100
    ) < 0.1

    # --------------------------------------------------
    # EXPORT CSV
    # --------------------------------------------------

    csv_file = (
        REPORT_DIR / "03_regional_performance.csv"
    )

    df.to_csv(csv_file, index=False)

    # --------------------------------------------------
    # CREATE AUTOMATED INSIGHTS REPORT
    # --------------------------------------------------

    md_file = (
        REPORT_DIR / "03_regional_insights.md"
    )

    lines = [
        "# InsightPilot - Regional Sales Analysis",
        "",
        "## Dataset",
        "",
        "Synthetic Canadian retail transactions "
        "from January 2025 through October 2026.",
        "",
        "## Key Findings",
        "",
        f"- Highest revenue region: {top_revenue['region']}",
        f"- Highest profit region: {top_profit['region']}",
        (
            f"- Highest margin: {top_margin['region']} "
            f"({top_margin['profit_margin_pct']:.2f}%)"
        ),
        (
            f"- Lowest margin: {lowest_margin['region']} "
            f"({lowest_margin['profit_margin_pct']:.2f}%)"
        ),
        (
            f"- Top regional revenue share: "
            f"{top_revenue['revenue_share_pct']:.2f}%"
        ),
        f"- Total revenue: CAD ${total_revenue:,.2f}",
        f"- Total profit: CAD ${total_profit:,.2f}",
        "",
        "## Regional Performance",
        "",
        "| Region | Orders | Revenue (CAD) | "
        "Profit (CAD) | Margin | Revenue Share |",
        "|---|---:|---:|---:|---:|---:|",
    ]

    for _, row in df.iterrows():
        lines.append(
            f"| {row['region']} "
            f"| {int(row['total_orders']):,} "
            f"| ${row['total_revenue']:,.2f} "
            f"| ${row['total_profit']:,.2f} "
            f"| {row['profit_margin_pct']:.2f}% "
            f"| {row['revenue_share_pct']:.2f}% |"
        )

    lines.extend([
        "",
        "## Business Interpretation",
        "",
        "Regions with high revenue do not necessarily "
        "have the highest profit margins.",
        "",
        "Investigate regional pricing, product mix, "
        "promotions, and operating costs before "
        "making business decisions.",
        "",
        "Customer counts are distinct within each "
        "region and may overlap across regions.",
        "",
        "**Important:** All data is synthetic. "
        "Regional differences are simulated and "
        "do not represent actual market performance.",
    ])

    md_file.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8"
    )

    print("\n" + "=" * 72)
    print("REPORT GENERATION COMPLETE")
    print("=" * 72)

    print("\nFiles created:")
    print("03_regional_performance.csv")
    print("03_regional_insights.md")

    print("\nSUCCESS! REGIONAL ANALYSIS COMPLETE")

finally:
    con.close()
