
from pathlib import Path
import subprocess
import sys

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx


# --------------------------------------------------
# INSIGHTPILOT - INTERACTIVE ANALYTICS DASHBOARD
# --------------------------------------------------

ROOT = Path(__file__).resolve().parent
DB_FILE = ROOT / "data" / "insightpilot.duckdb"


@st.cache_data
def load_data(database_path, database_modified):
    con = duckdb.connect(database_path, read_only=True)

    try:
        query = """
        SELECT
            o.order_id,
            o.order_date,
            o.customer_id,
            o.region,
            o.channel,
            o.quantity,
            o.discount_pct,
            o.revenue,
            o.profit,
            p.product_name,
            p.category
        FROM orders o
        JOIN products p
            ON o.product_id = p.product_id
        ORDER BY o.order_date
        """

        df = con.execute(query).fetchdf()
        df["order_date"] = pd.to_datetime(df["order_date"])
        return df

    finally:
        con.close()


def main():

    st.set_page_config(
        page_title="InsightPilot | Business Intelligence",
        page_icon="📊",
        layout="wide",
    )

    st.title("📊 InsightPilot")
    st.subheader("AI-Powered Retail Intelligence Platform")

    st.caption(
        "Interactive business intelligence dashboard | "
        "Synthetic Canadian retail data"
    )

    if not DB_FILE.exists():
        st.error(
            "SQL database not found. "
            "Run 01_build_database.py first."
        )
        st.stop()

    df = load_data(
        str(DB_FILE),
        DB_FILE.stat().st_mtime,
    )

    if df.empty:
        st.error("No records found in the database.")
        st.stop()

    # --------------------------------------------------
    # SIDEBAR FILTERS
    # --------------------------------------------------

    st.sidebar.header("Dashboard Filters")

    min_date = df["order_date"].min().date()
    max_date = df["order_date"].max().date()

    date_range = st.sidebar.date_input(
        "Order Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    if len(date_range) != 2:
        st.info("Please select both start and end dates.")
        st.stop()

    start_date, end_date = date_range

    categories = sorted(df["category"].unique().tolist())
    regions = sorted(df["region"].unique().tolist())
    channels = sorted(df["channel"].unique().tolist())

    selected_categories = st.sidebar.multiselect(
        "Product Categories",
        options=categories,
        default=categories,
    )

    selected_regions = st.sidebar.multiselect(
        "Regions",
        options=regions,
        default=regions,
    )

    selected_channels = st.sidebar.multiselect(
        "Sales Channels",
        options=channels,
        default=channels,
    )

    # --------------------------------------------------
    # APPLY FILTERS
    # --------------------------------------------------

    filtered = df[
        (df["order_date"].dt.date >= start_date)
        & (df["order_date"].dt.date <= end_date)
        & (df["category"].isin(selected_categories))
        & (df["region"].isin(selected_regions))
        & (df["channel"].isin(selected_channels))
    ].copy()

    if filtered.empty:
        st.warning("No records match the selected filters.")
        st.stop()

    # --------------------------------------------------
    # BUSINESS KPI CARDS
    # --------------------------------------------------

    total_revenue = filtered["revenue"].sum()
    total_profit = filtered["profit"].sum()
    total_orders = filtered["order_id"].nunique()

    profit_margin = (
        total_profit / total_revenue * 100
        if total_revenue > 0
        else 0
    )

    unique_customers = filtered["customer_id"].nunique()

    st.markdown("### Executive KPI Overview")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Total Revenue",
        f"CAD ${total_revenue:,.0f}"
    )

    c2.metric(
        "Total Profit",
        f"CAD ${total_profit:,.0f}"
    )

    c3.metric(
        "Total Orders",
        f"{total_orders:,}"
    )

    c4.metric(
        "Profit Margin",
        f"{profit_margin:.2f}%"
    )

    st.caption(
        f"Unique customers in filtered data: "
        f"{unique_customers:,}"
    )

    st.divider()

    # --------------------------------------------------
    # MONTHLY REVENUE TREND
    # --------------------------------------------------

    st.markdown("### Monthly Sales Performance")

    monthly = (
        filtered.assign(
            month=filtered["order_date"]
            .dt.to_period("M")
            .dt.to_timestamp()
        )
        .groupby("month", as_index=False)
        .agg(
            revenue=("revenue", "sum"),
            profit=("profit", "sum"),
        )
    )

    fig_monthly = px.line(
        monthly,
        x="month",
        y="revenue",
        markers=True,
        title="Monthly Revenue Trend",
        labels={
            "month": "Month",
            "revenue": "Revenue (CAD)",
        },
    )

    fig_monthly.update_layout(height=380)

    st.plotly_chart(
        fig_monthly,
        width="stretch",
    )

    # --------------------------------------------------
    # CATEGORY PERFORMANCE
    # --------------------------------------------------

    category_df = (
        filtered.groupby("category", as_index=False)
        .agg(
            revenue=("revenue", "sum"),
            profit=("profit", "sum"),
        )
        .sort_values("revenue", ascending=False)
    )

    category_df["margin_pct"] = (
        category_df["profit"]
        / category_df["revenue"]
        * 100
    )

    fig_category = px.bar(
        category_df,
        x="category",
        y="revenue",
        color="category",
        title="Revenue by Product Category",
        labels={
            "category": "Category",
            "revenue": "Revenue (CAD)",
        },
    )

    # --------------------------------------------------
    # REGIONAL PROFITABILITY
    # --------------------------------------------------

    region_df = (
        filtered.groupby("region", as_index=False)
        .agg(
            revenue=("revenue", "sum"),
            profit=("profit", "sum"),
        )
        .sort_values("profit", ascending=False)
    )

    region_df["margin_pct"] = (
        region_df["profit"]
        / region_df["revenue"]
        * 100
    )

    fig_region = px.bar(
        region_df,
        x="region",
        y="profit",
        color="region",
        title="Profit by Canadian Region",
        labels={
            "region": "Region",
            "profit": "Profit (CAD)",
        },
    )

    left, right = st.columns(2)

    with left:
        st.plotly_chart(
            fig_category,
            width="stretch",
        )

    with right:
        st.plotly_chart(
            fig_region,
            width="stretch",
        )

    # --------------------------------------------------
    # SALES CHANNEL PERFORMANCE
    # --------------------------------------------------

    st.markdown("### Sales Channel Distribution")

    channel_df = (
        filtered.groupby("channel", as_index=False)
        .agg(revenue=("revenue", "sum"))
    )

    fig_channel = px.pie(
        channel_df,
        names="channel",
        values="revenue",
        hole=0.45,
        title="Revenue Share by Sales Channel",
    )

    st.plotly_chart(
        fig_channel,
        width="stretch",
    )

    st.divider()

    # --------------------------------------------------
    # DISCOUNT ANOMALY MONITOR
    # --------------------------------------------------

    st.markdown("### Discount Anomaly Monitor")

    st.caption(
        "Historical baseline: Electronics monthly "
        "average discounts before September 2026. "
        "Results respond to dashboard filters."
    )

    electronics = filtered[
        filtered["category"] == "Electronics"
    ].copy()

    if electronics.empty:
        st.info(
            "Select Electronics to view discount monitoring."
        )
    else:
        electronics["month"] = (
            electronics["order_date"]
            .dt.to_period("M")
            .dt.to_timestamp()
        )

        discount_monthly = (
            electronics.groupby("month", as_index=False)
            .agg(
                avg_discount_pct=("discount_pct", "mean")
            )
            .sort_values("month")
        )

        event_month = pd.Timestamp("2026-09-01")

        baseline = discount_monthly[
            discount_monthly["month"] < event_month
        ]

        if len(baseline) < 6:
            st.info(
                "At least six historical months are needed "
                "to calculate the anomaly baseline."
            )
        else:
            mean_discount = baseline[
                "avg_discount_pct"
            ].mean()

            std_discount = baseline[
                "avg_discount_pct"
            ].std(ddof=1)

            threshold = (
                mean_discount + 3 * std_discount
            )

            discount_monthly["is_anomaly"] = (
                discount_monthly["avg_discount_pct"]
                > threshold
            )

            a1, a2 = st.columns(2)

            a1.metric(
                "Historical Average Discount",
                f"{mean_discount:.2f}%"
            )

            a2.metric(
                "Anomaly Alert Threshold",
                f"{threshold:.2f}%"
            )

            fig_discount = px.line(
                discount_monthly,
                x="month",
                y="avg_discount_pct",
                markers=True,
                title="Electronics Monthly Average Discount",
                labels={
                    "month": "Month",
                    "avg_discount_pct": "Discount (%)",
                },
            )

            fig_discount.add_hline(
                y=threshold,
                line_dash="dash",
                annotation_text="3-Sigma Threshold",
            )

            st.plotly_chart(
                fig_discount,
                width="stretch",
            )

            flagged = discount_monthly[
                discount_monthly["is_anomaly"]
            ]

            if not flagged.empty:
                st.warning(
                    f"{len(flagged)} monthly discount "
                    "anomaly alert(s) detected."
                )

                st.dataframe(
                    flagged,
                    hide_index=True,
                    width="stretch",
                )
            else:
                st.success(
                    "No discount anomalies found "
                    "for the selected filters."
                )

    st.divider()

    # --------------------------------------------------
    # DATA EXPLORER
    # --------------------------------------------------

    st.markdown("### Transaction Data Explorer")

    st.caption(
        "Preview of the 25 most recent filtered orders."
    )

    preview = (
        filtered.sort_values(
            "order_date", ascending=False
        )
        .head(25)
    )

    st.dataframe(
        preview,
        hide_index=True,
        width="stretch",
    )

    st.download_button(
        label="Download Filtered Transactions",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="insightpilot_filtered_orders.csv",
        mime="text/csv",
    )

    st.divider()

    # --------------------------------------------------
    # INSIGHTPILOT - SQL ANALYTICS COPILOT
    # --------------------------------------------------

    from src.copilot_engine import answer_question

    st.markdown("### 🤖 InsightPilot Analytics Copilot")

    st.caption(
        "Ask business questions and receive SQL-grounded "
        "answers using our synthetic retail database. "
        "Copilot answers currently use the complete dataset "
        "and do not follow dashboard sidebar filters."
    )

    st.markdown("#### Ask a Business Question")

    with st.form("insightpilot_copilot_form"):

        question = st.text_input(
            "Your question",
            placeholder=(
                "Which category has the highest revenue?"
            ),
        )

        submitted = st.form_submit_button(
            "Analyze Question"
        )

    if submitted:

        with st.spinner("Analyzing business data..."):

            response = answer_question(question)

            st.session_state["copilot_response"] = response

    if "copilot_response" in st.session_state:

        st.markdown("#### Copilot Response")

        st.text(
            st.session_state["copilot_response"]
        )

    st.info(
        "InsightPilot currently uses predefined, read-only "
        "SQL queries to generate verified business insights. "
        "Generative AI capabilities are a separate enhancement."
    )

    st.divider()


    st.caption(
        "InsightPilot | Synthetic business data | "
        "For demonstration and educational purposes. "
        "Statistical alerts are not evidence of fraud."
    )


# --------------------------------------------------
# ALLOW VS CODE'S PYTHON RUN BUTTON
# --------------------------------------------------

if __name__ == "__main__":
    if get_script_run_ctx() is None:
        print("Launching InsightPilot dashboard...")

        subprocess.run(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                str(Path(__file__).resolve()),
            ],
            check=False,
        )
    else:
        main()
