
from pathlib import Path
import pandas as pd

# ============================================================
# PROJECT CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

PROCESSED_DIR = BASE_DIR / "data" / "processed"
ANALYTICS_DIR = BASE_DIR / "data" / "analytics"

ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# ANALYTICS MODEL
# ============================================================

def create_fact_sales():

    print("=" * 60)
    print("BRAZILIAN E-COMMERCE | ANALYTICS MODEL")
    print("=" * 60)

    # Load processed datasets
    orders = pd.read_csv(
        PROCESSED_DIR / "orders.csv",
        parse_dates=["order_purchase_timestamp"]
    )

    items = pd.read_csv(
        PROCESSED_DIR / "order_items.csv"
    )

    customers = pd.read_csv(
        PROCESSED_DIR / "customers.csv"
    )

    products = pd.read_csv(
        PROCESSED_DIR / "products.csv"
    )

    sellers = pd.read_csv(
        PROCESSED_DIR / "sellers.csv"
    )

    # Merge order items with orders
    fact_sales = items.merge(
        orders[
            [
                "order_id",
                "customer_id",
                "order_status",
                "order_purchase_timestamp"
            ]
        ],
        on="order_id",
        how="left",
        validate="many_to_one"
    )

    # Add customer attributes
    fact_sales = fact_sales.merge(
        customers[
            [
                "customer_id",
                "customer_unique_id",
                "customer_state"
            ]
        ],
        on="customer_id",
        how="left",
        validate="many_to_one"
    )

    # Add product attributes
    fact_sales = fact_sales.merge(
        products[
            [
                "product_id",
                "product_category_name"
            ]
        ],
        on="product_id",
        how="left",
        validate="many_to_one"
    )

    # Add seller attributes
    fact_sales = fact_sales.merge(
        sellers[
            [
                "seller_id",
                "seller_state"
            ]
        ],
        on="seller_id",
        how="left",
        validate="many_to_one"
    )

    # Calculate item revenue
    fact_sales["item_revenue"] = fact_sales["price"]

    # Calculate total item value including freight
    fact_sales["item_total_value"] = (
        fact_sales["price"]
        + fact_sales["freight_value"]
    )

    # Extract date attributes
    fact_sales["purchase_date"] = (
        fact_sales["order_purchase_timestamp"].dt.date
    )

    fact_sales["purchase_year"] = (
        fact_sales["order_purchase_timestamp"].dt.year
    )

    fact_sales["purchase_month"] = (
        fact_sales["order_purchase_timestamp"].dt.month
    )

    fact_sales["purchase_year_month"] = (
        fact_sales["order_purchase_timestamp"].dt.to_period("M").astype(str)
    )

    # Save analytical fact table
    output_path = ANALYTICS_DIR / "fact_sales.csv"

    fact_sales.to_csv(output_path, index=False)

    # Summary
    print(f"\nFact table: fact_sales")
    print(f"Rows: {len(fact_sales):,}")
    print(f"Columns: {len(fact_sales.columns)}")
    print(f"Revenue: R$ {fact_sales['item_revenue'].sum():,.2f}")
    print(f"Saved: {output_path}")

    print("\nANALYTICS MODEL COMPLETED")
    print("=" * 60)

    return fact_sales


# ============================================================
# EXECUTION
# ============================================================

if __name__ == "__main__":
    fact_sales = create_fact_sales()
