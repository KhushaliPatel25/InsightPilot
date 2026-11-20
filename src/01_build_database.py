
from pathlib import Path
import duckdb

# --------------------------------------------------
# INSIGHTPILOT - SQL DATABASE SETUP
# --------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

ORDERS_FILE = DATA_DIR / "orders.csv"
PRODUCTS_FILE = DATA_DIR / "products.csv"
DB_FILE = DATA_DIR / "insightpilot.duckdb"

print("=" * 60)
print("INSIGHTPILOT - SQL DATABASE SETUP")
print("=" * 60)

# Verify source files
for file in [ORDERS_FILE, PRODUCTS_FILE]:
    if not file.exists():
        raise FileNotFoundError(
            f"Missing dataset: {file.name}. "
            "Run generate_data.py first."
        )

# Connect to local database
con = duckdb.connect(str(DB_FILE))

try:
    # --------------------------------------------------
    # CREATE PRODUCTS TABLE
    # --------------------------------------------------

    con.execute(
        """
        CREATE OR REPLACE TABLE products AS
        SELECT
            CAST(product_id AS VARCHAR) AS product_id,
            CAST(product_name AS VARCHAR) AS product_name,
            CAST(category AS VARCHAR) AS category,
            CAST(unit_price AS DOUBLE) AS unit_price,
            CAST(unit_cost AS DOUBLE) AS unit_cost
        FROM read_csv_auto(?)
        """,
        [str(PRODUCTS_FILE)],
    )

    print("\nProducts table created successfully.")

    # --------------------------------------------------
    # CREATE ORDERS TABLE
    # --------------------------------------------------

    con.execute(
        """
        CREATE OR REPLACE TABLE orders AS
        SELECT
            CAST(order_id AS VARCHAR) AS order_id,
            CAST(order_date AS DATE) AS order_date,
            CAST(customer_id AS VARCHAR) AS customer_id,
            CAST(product_id AS VARCHAR) AS product_id,
            CAST(region AS VARCHAR) AS region,
            CAST(channel AS VARCHAR) AS channel,
            CAST(quantity AS INTEGER) AS quantity,
            CAST(discount_pct AS DOUBLE) AS discount_pct,
            CAST(revenue AS DOUBLE) AS revenue,
            CAST(profit AS DOUBLE) AS profit
        FROM read_csv_auto(?)
        """,
        [str(ORDERS_FILE)],
    )

    print("Orders table created successfully.")

    # --------------------------------------------------
    # VALIDATE RECORD COUNTS
    # --------------------------------------------------

    order_count = con.execute(
        "SELECT COUNT(*) FROM orders"
    ).fetchone()[0]

    product_count = con.execute(
        "SELECT COUNT(*) FROM products"
    ).fetchone()[0]

    # --------------------------------------------------
    # DATA QUALITY CHECKS
    # --------------------------------------------------

    missing_values = con.execute(
        """
        SELECT COUNT(*)
        FROM orders
        WHERE order_id IS NULL
           OR order_date IS NULL
           OR customer_id IS NULL
           OR product_id IS NULL
           OR revenue IS NULL
           OR profit IS NULL
        """
    ).fetchone()[0]

    duplicate_orders = con.execute(
        """
        SELECT COUNT(*) - COUNT(DISTINCT order_id)
        FROM orders
        """
    ).fetchone()[0]

    unmatched_products = con.execute(
        """
        SELECT COUNT(*)
        FROM orders o
        LEFT JOIN products p
            ON o.product_id = p.product_id
        WHERE p.product_id IS NULL
        """
    ).fetchone()[0]

    # --------------------------------------------------
    # BUSINESS METRICS
    # --------------------------------------------------

    metrics = con.execute(
        """
        SELECT
            ROUND(SUM(revenue), 2),
            ROUND(SUM(profit), 2),
            COUNT(DISTINCT customer_id),
            COUNT(DISTINCT region),
            COUNT(DISTINCT channel)
        FROM orders
        """
    ).fetchone()

    total_revenue = metrics[0]
    total_profit = metrics[1]
    customers = metrics[2]
    regions = metrics[3]
    channels = metrics[4]

    # --------------------------------------------------
    # DISPLAY RESULTS
    # --------------------------------------------------

    print("\n" + "=" * 60)
    print("DATABASE VALIDATION RESULTS")
    print("=" * 60)

    print(f"Total Orders: {order_count:,}")
    print(f"Total Products: {product_count}")
    print(f"Missing Required Values: {missing_values}")
    print(f"Duplicate Order IDs: {duplicate_orders}")
    print(f"Unmatched Product IDs: {unmatched_products}")

    print("\n" + "=" * 60)
    print("BUSINESS KPI SUMMARY")
    print("=" * 60)

    print(f"Total Revenue: CAD ${total_revenue:,.2f}")
    print(f"Total Profit: CAD ${total_profit:,.2f}")
    print(f"Unique Customers: {customers:,}")
    print(f"Regions: {regions}")
    print(f"Sales Channels: {channels}")

    # Final validation assertions
    assert order_count == 15000
    assert product_count == 16
    assert missing_values == 0
    assert duplicate_orders == 0
    assert unmatched_products == 0

    print("\n" + "=" * 60)
    print("SUCCESS! SQL DATABASE VALIDATED")
    print("=" * 60)

finally:
    con.close()
