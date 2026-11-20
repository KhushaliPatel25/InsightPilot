
from pathlib import Path
import duckdb

# --------------------------------------------------
# INSIGHTPILOT - CATEGORY PERFORMANCE ANALYSIS
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
print("INSIGHTPILOT - CATEGORY PERFORMANCE ANALYSIS")
print("=" * 72)

# --------------------------------------------------
# CONNECT TO DATABASE
# --------------------------------------------------

con = duckdb.connect(str(DB_FILE), read_only=True)

try:
    # --------------------------------------------------
    # SQL CATEGORY ANALYSIS
    # --------------------------------------------------

    query = """
    SELECT
        p.category,
        COUNT(*) AS total_orders,
        SUM(o.quantity) AS units_sold,
        ROUND(SUM(o.revenue), 2) AS total_revenue,
        ROUND(SUM(o.profit), 2) AS total_profit,
        ROUND(
            100.0 * SUM(o.profit)
            / NULLIF(SUM(o.revenue), 0),
            2
        ) AS profit_margin_pct
    FROM orders o
    INNER JOIN products p
        ON o.product_id = p.product_id
    GROUP BY p.category
    ORDER BY total_revenue DESC
    """

    df = con.execute(query).fetchdf()

    if df.empty:
        raise ValueError("Category analysis returned no records.")

    # --------------------------------------------------
    # DISPLAY RESULTS
    # --------------------------------------------------

    print("\nCATEGORY PERFORMANCE SUMMARY\n")

    for _, row in df.iterrows():
        print("-" * 55)
        print(f"Category: {row['category']}")
        print(f"Orders: {int(row['total_orders']):,}")
        print(f"Units Sold: {int(row['units_sold']):,}")
        print(f"Revenue: CAD ${row['total_revenue']:,.2f}")
        print(f"Profit: CAD ${row['total_profit']:,.2f}")
        print(
            f"Profit Margin: "
            f"{row['profit_margin_pct']:.2f}%"
        )

    # --------------------------------------------------
    # IDENTIFY KEY BUSINESS INSIGHTS
    # --------------------------------------------------

    top_revenue = df.loc[df["total_revenue"].idxmax()]
    top_profit = df.loc[df["total_profit"].idxmax()]
    top_margin = df.loc[df["profit_margin_pct"].idxmax()]
    lowest_margin = df.loc[df["profit_margin_pct"].idxmin()]

    total_revenue = df["total_revenue"].sum()
    total_profit = df["total_profit"].sum()

    print("\n" + "=" * 72)
    print("KEY BUSINESS INSIGHTS")
    print("=" * 72)

    print(
        f"\nHighest Revenue Category: "
        f"{top_revenue['category']}"
    )

    print(
        f"Highest Profit Category: "
        f"{top_profit['category']}"
    )

    print(
        f"Highest Profit Margin: "
        f"{top_margin['category']} "
        f"({top_margin['profit_margin_pct']:.2f}%)"
    )

    print(
        f"Lowest Profit Margin: "
        f"{lowest_margin['category']} "
        f"({lowest_margin['profit_margin_pct']:.2f}%)"
    )

    print(f"\nTotal Revenue: CAD ${total_revenue:,.2f}")
    print(f"Total Profit: CAD ${total_profit:,.2f}")

    # --------------------------------------------------
    # EXPORT CSV REPORT
    # --------------------------------------------------

    csv_file = REPORT_DIR / "02_category_performance.csv"

    df.to_csv(csv_file, index=False)

    # --------------------------------------------------
    # EXPORT MARKDOWN INSIGHTS REPORT
    # --------------------------------------------------

    md_file = REPORT_DIR / "02_category_insights.md"

    insights = [
        "# InsightPilot - Category Performance",
        "",
        "## Dataset",
        "",
        "Synthetic retail transactions from "
        "January 2025 through October 2026.",
        "",
        "## Key Findings",
        "",
        f"- Highest revenue: {top_revenue['category']}",
        f"- Highest profit: {top_profit['category']}",
        (
            f"- Highest profit margin: "
            f"{top_margin['category']} "
            f"({top_margin['profit_margin_pct']:.2f}%)"
        ),
        (
            f"- Lowest profit margin: "
            f"{lowest_margin['category']} "
            f"({lowest_margin['profit_margin_pct']:.2f}%)"
        ),
        f"- Total revenue: CAD ${total_revenue:,.2f}",
        f"- Total profit: CAD ${total_profit:,.2f}",
        "",
        "## Category Performance",
        "",
        "| Category | Revenue (CAD) | Profit (CAD) | Margin |",
        "|---|---:|---:|---:|",
    ]

    for _, row in df.iterrows():
        insights.append(
            f"| {row['category']} "
            f"| ${row['total_revenue']:,.2f} "
            f"| ${row['total_profit']:,.2f} "
            f"| {row['profit_margin_pct']:.2f}% |"
        )

    insights.extend([
        "",
        "## Interpretation",
        "",
        "Revenue leadership does not necessarily "
        "mean margin leadership. Categories with "
        "lower margins may require further review "
        "of pricing, costs, and discounts.",
        "",
        "**Note:** All findings are based on "
        "synthetically generated data.",
    ])

    md_file.write_text(
        "\n".join(insights) + "\n",
        encoding="utf-8"
    )

    print("\n" + "=" * 72)
    print("REPORT GENERATION COMPLETE")
    print("=" * 72)

    print("\nGenerated files:")
    print("02_category_performance.csv")
    print("02_category_insights.md")

    print("\nSUCCESS! CATEGORY ANALYSIS COMPLETE")

finally:
    con.close()
