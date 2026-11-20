
from pathlib import Path
import duckdb

# --------------------------------------------------
# INSIGHTPILOT - SQL-GROUNDED ANALYTICS COPILOT
# --------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
DB_FILE = ROOT / "data" / "insightpilot.duckdb"


def answer_question(question):
    """
    Answer supported business questions using
    predefined, read-only SQL queries.

    Answers currently cover the full dataset.
    """

    if not DB_FILE.exists():
        return (
            "Database not found. Run "
            "01_build_database.py first."
        )

    question = question.strip().lower()

    if not question:
        return "Please enter a business question."

    con = duckdb.connect(str(DB_FILE), read_only=True)

    try:

        # ------------------------------------------
        # DISCOUNT ANOMALY QUESTION
        # ------------------------------------------

        if any(
            word in question
            for word in ["discount", "anomaly", "promotion"]
        ):

            result = con.execute(
                """
                WITH monthly_discounts AS (
                    SELECT
                        DATE_TRUNC(
                            'month', o.order_date
                        )::DATE AS month,
                        AVG(o.discount_pct)
                            AS avg_discount
                    FROM orders o
                    JOIN products p
                        ON o.product_id = p.product_id
                    WHERE p.category = 'Electronics'
                    GROUP BY 1
                )
                SELECT
                    ROUND(AVG(
                        CASE
                            WHEN month < DATE '2026-09-01'
                            THEN avg_discount
                        END
                    ), 2) AS baseline_discount,
                    ROUND(MAX(
                        CASE
                            WHEN month = DATE '2026-09-01'
                            THEN avg_discount
                        END
                    ), 2) AS september_discount
                FROM monthly_discounts
                """
            ).fetchone()

            baseline, september = result

            if baseline is None or september is None:
                return "Insufficient discount data."

            difference = september - baseline

            return (
                "ELECTRONICS DISCOUNT ANALYSIS\n\n"
                f"Historical monthly average: {baseline:.2f}%\n"
                f"September 2026 average: {september:.2f}%\n"
                f"Increase: {difference:.2f} percentage points\n\n"
                "Finding: September 2026 shows an "
                "unusually large promotional discount.\n\n"
                "Recommendation: Review promotional "
                "pricing and its effect on profitability.\n\n"
                "Note: This anomaly was intentionally "
                "introduced into synthetic data."
            )

        # ------------------------------------------
        # CATEGORY PERFORMANCE QUESTION
        # ------------------------------------------

        elif "category" in question or "categories" in question:

            rows = con.execute(
                """
                SELECT
                    p.category,
                    ROUND(SUM(o.revenue), 2) AS revenue,
                    ROUND(SUM(o.profit), 2) AS profit
                FROM orders o
                JOIN products p
                    ON o.product_id = p.product_id
                GROUP BY p.category
                ORDER BY revenue DESC
                """
            ).fetchall()

            if not rows:
                return "No category data available."

            top_revenue = rows[0]
            top_profit = max(rows, key=lambda row: row[2])

            return (
                "CATEGORY PERFORMANCE ANALYSIS\n\n"
                f"Highest revenue category: {top_revenue[0]}\n"
                f"Revenue: CAD ${top_revenue[1]:,.2f}\n\n"
                f"Highest profit category: {top_profit[0]}\n"
                f"Profit: CAD ${top_profit[2]:,.2f}\n\n"
                "Recommendation: Compare category "
                "revenue, profit margins, and discounts "
                "before allocating additional resources."
            )

        # ------------------------------------------
        # REGIONAL PERFORMANCE QUESTION
        # ------------------------------------------

        elif "region" in question or "province" in question:

            result = con.execute(
                """
                SELECT
                    region,
                    ROUND(SUM(revenue), 2) AS revenue,
                    ROUND(SUM(profit), 2) AS profit,
                    ROUND(
                        100 * SUM(profit)
                        / NULLIF(SUM(revenue), 0),
                        2
                    ) AS profit_margin
                FROM orders
                GROUP BY region
                ORDER BY profit DESC
                LIMIT 1
                """
            ).fetchone()

            if result is None:
                return "No regional data available."

            region, revenue, profit, margin = result

            return (
                "REGIONAL PROFITABILITY ANALYSIS\n\n"
                f"Highest profit region: {region}\n"
                f"Revenue: CAD ${revenue:,.2f}\n"
                f"Profit: CAD ${profit:,.2f}\n"
                f"Profit margin: {margin:.2f}%\n\n"
                "Recommendation: Compare product mix "
                "and regional profitability before "
                "making expansion decisions."
            )

        # ------------------------------------------
        # SALES CHANNEL QUESTION
        # ------------------------------------------

        elif "channel" in question:

            result = con.execute(
                """
                SELECT
                    channel,
                    ROUND(SUM(revenue), 2) AS revenue,
                    ROUND(SUM(profit), 2) AS profit
                FROM orders
                GROUP BY channel
                ORDER BY revenue DESC
                LIMIT 1
                """
            ).fetchone()

            if result is None:
                return "No channel data available."

            channel, revenue, profit = result

            return (
                "SALES CHANNEL PERFORMANCE\n\n"
                f"Highest revenue channel: {channel}\n"
                f"Revenue: CAD ${revenue:,.2f}\n"
                f"Profit: CAD ${profit:,.2f}\n\n"
                "Recommendation: Compare revenue "
                "and profitability across channels "
                "before increasing investment."
            )

        # ------------------------------------------
        # MONTHLY REVENUE TREND QUESTION
        # ------------------------------------------

        elif any(
            word in question
            for word in ["monthly", "trend", "growth"]
        ):

            rows = con.execute(
                """
                SELECT
                    DATE_TRUNC(
                        'month', order_date
                    )::DATE AS month,
                    ROUND(SUM(revenue), 2) AS revenue
                FROM orders
                GROUP BY 1
                ORDER BY month DESC
                LIMIT 2
                """
            ).fetchall()

            if len(rows) < 2:
                return "Insufficient monthly data."

            latest, previous = rows

            growth = (
                (latest[1] - previous[1])
                / previous[1] * 100
                if previous[1] != 0
                else 0
            )

            return (
                "MONTHLY REVENUE TREND\n\n"
                f"Latest month: {latest[0]}\n"
                f"Revenue: CAD ${latest[1]:,.2f}\n\n"
                f"Previous month: {previous[0]}\n"
                f"Revenue: CAD ${previous[1]:,.2f}\n\n"
                f"Month-over-month change: {growth:+.2f}%\n\n"
                "Note: This comparison covers "
                "the two most recent months."
            )

        # ------------------------------------------
        # OVERALL BUSINESS KPI QUESTION
        # ------------------------------------------

        elif any(
            word in question
            for word in [
                "revenue", "sales", "profit",
                "orders", "kpi", "total"
            ]
        ):

            result = con.execute(
                """
                SELECT
                    ROUND(SUM(revenue), 2),
                    ROUND(SUM(profit), 2),
                    COUNT(DISTINCT order_id),
                    ROUND(
                        100 * SUM(profit)
                        / NULLIF(SUM(revenue), 0),
                        2
                    )
                FROM orders
                """
            ).fetchone()

            revenue, profit, orders, margin = result

            return (
                "EXECUTIVE BUSINESS KPI SUMMARY\n\n"
                f"Total revenue: CAD ${revenue:,.2f}\n"
                f"Total profit: CAD ${profit:,.2f}\n"
                f"Total orders: {orders:,}\n"
                f"Profit margin: {margin:.2f}%\n\n"
                "These figures are calculated "
                "directly from the SQL database."
            )

        # ------------------------------------------
        # UNSUPPORTED QUESTION
        # ------------------------------------------

        else:

            return (
                "I can currently answer questions about:\n\n"
                "- Overall revenue, profit, and orders\n"
                "- Product category performance\n"
                "- Regional profitability\n"
                "- Sales channel performance\n"
                "- Monthly revenue trends\n"
                "- Electronics discount anomalies\n\n"
                "Please ask one of these questions."
            )

    finally:
        con.close()


# --------------------------------------------------
# TEST THE COPILOT ENGINE
# --------------------------------------------------

def main():

    print("=" * 65)
    print("INSIGHTPILOT - ANALYTICS COPILOT TEST")
    print("=" * 65)

    questions = [
        "What are our total sales and profit?",
        "Which category has the highest revenue?",
        "Which region has the highest profit?",
        "Which sales channel performs best?",
        "How is our monthly revenue trending?",
        "What happened to Electronics discounts "
        "in September 2026?",
    ]

    for number, question in enumerate(questions, start=1):

        print("\n" + "=" * 65)
        print(f"QUESTION {number}: {question}")
        print("=" * 65)

        response = answer_question(question)
        print(response)

    print("\n" + "=" * 65)
    print("SUCCESS! COPILOT ENGINE TEST COMPLETE")
    print("=" * 65)


if __name__ == "__main__":
    main()
