
from pathlib import Path
from datetime import date, timedelta
import csv
import random

# Project locations
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Reproducible synthetic dataset
rng = random.Random(42)

products = [
    ("P001", "Wireless Mouse", "Electronics", 29.99, 13.00),
    ("P002", "Bluetooth Speaker", "Electronics", 79.99, 41.00),
    ("P003", "Mechanical Keyboard", "Electronics", 109.99, 57.00),
    ("P004", "Portable Charger", "Electronics", 39.99, 19.00),
    ("P005", "Air Fryer", "Home", 129.99, 73.00),
    ("P006", "Desk Lamp", "Home", 44.99, 21.00),
    ("P007", "Coffee Grinder", "Home", 69.99, 34.00),
    ("P008", "Storage Organizer", "Home", 24.99, 10.00),
    ("P009", "Skincare Set", "Beauty", 49.99, 23.00),
    ("P010", "Hair Dryer", "Beauty", 89.99, 45.00),
    ("P011", "Face Cleanser", "Beauty", 19.99, 8.00),
    ("P012", "Body Lotion", "Beauty", 22.99, 9.00),
    ("P013", "Yoga Mat", "Sports", 34.99, 15.00),
    ("P014", "Resistance Bands", "Sports", 24.99, 9.00),
    ("P015", "Dumbbell Set", "Sports", 99.99, 58.00),
    ("P016", "Water Bottle", "Sports", 27.99, 11.00),
]

regions = [
    "Ontario",
    "Quebec",
    "British Columbia",
    "Alberta",
    "Atlantic Canada",
]

channels = ["Online", "Retail Store", "Marketplace"]

# Save product information
with (DATA_DIR / "products.csv").open(
    "w", newline="", encoding="utf-8"
) as file:
    writer = csv.writer(file)
    writer.writerow([
        "product_id", "product_name", "category",
        "unit_price", "unit_cost"
    ])
    writer.writerows(products)

# Generate historical orders
start_date = date(2025, 1, 1)
end_date = date(2026, 10, 31)
date_range = (end_date - start_date).days

orders = []

for i in range(1, 15001):
    order_date = start_date + timedelta(
        days=rng.randint(0, date_range)
    )

    product = rng.choice(products)

    product_id = product[0]
    category = product[2]
    unit_price = product[3]
    unit_cost = product[4]

    quantity = rng.choices(
        [1, 2, 3, 4, 5],
        weights=[40, 30, 15, 10, 5]
    )[0]

    discount_pct = rng.choice([0, 0, 0, 5, 10, 15])

    # Simulated promotional discount anomaly
    if (
        order_date.year == 2026
        and order_date.month == 9
        and category == "Electronics"
    ):
        discount_pct = rng.choice([25, 30, 35])

    revenue = round(
        quantity * unit_price * (1 - discount_pct / 100),
        2
    )

    cost = round(quantity * unit_cost, 2)
    profit = round(revenue - cost, 2)

    orders.append([
        f"ORD{i:06d}",
        order_date.isoformat(),
        f"C{rng.randint(1, 3500):05d}",
        product_id,
        rng.choice(regions),
        rng.choice(channels),
        quantity,
        discount_pct,
        revenue,
        profit,
    ])

orders.sort(key=lambda row: (row[1], row[0]))

# Save transaction information
with (DATA_DIR / "orders.csv").open(
    "w", newline="", encoding="utf-8"
) as file:
    writer = csv.writer(file)

    writer.writerow([
        "order_id",
        "order_date",
        "customer_id",
        "product_id",
        "region",
        "channel",
        "quantity",
        "discount_pct",
        "revenue",
        "profit",
    ])

    writer.writerows(orders)

# Validate results
assert len(orders) == 15000
assert len(products) == 16
assert all(row[8] > 0 for row in orders)

total_revenue = sum(row[8] for row in orders)
total_profit = sum(row[9] for row in orders)

print("=" * 55)
print("INSIGHTPILOT - DATA GENERATION COMPLETE")
print("=" * 55)
print(f"Orders generated: {len(orders):,}")
print(f"Products generated: {len(products)}")
print(f"Total Revenue: CAD ${total_revenue:,.2f}")
print(f"Total Profit: CAD ${total_profit:,.2f}")
print(f"Date Range: {start_date} to {end_date}")
print("\nFiles created:")
print(DATA_DIR / "orders.csv")
print(DATA_DIR / "products.csv")
print("\nSUCCESS! Dataset ready for analysis.")
