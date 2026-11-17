
from pathlib import Path
import pandas as pd

# ============================================================
# ANALYTICS - DIMENSIONS
# Brazilian E-commerce (Olist)
# ============================================================

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"
ANALYTICS = ROOT / "data" / "analytics"

ANALYTICS.mkdir(parents=True, exist_ok=True)


# ============================================================
# LOAD DATA
# ============================================================

def load_data():
    customers = pd.read_csv(PROCESSED / "customers.csv")
    products = pd.read_csv(PROCESSED / "products.csv")
    sellers = pd.read_csv(PROCESSED / "sellers.csv")
    orders = pd.read_csv(PROCESSED / "orders.csv")

    return customers, products, sellers, orders


# ============================================================
# DIM_CUSTOMERS
# ============================================================

def create_dim_customers(customers):
    columns = [
        "customer_id",
        "customer_unique_id",
        "customer_zip_code_prefix",
        "customer_city",
        "customer_state"
    ]

    dim = customers[columns].copy()
    dim = dim.drop_duplicates(subset=["customer_id"])

    return dim


# ============================================================
# DIM_PRODUCTS
# ============================================================

def create_dim_products(products):
    columns = [
        "product_id",
        "product_category_name",
        "product_photos_qty",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm"
    ]

    dim = products[columns].copy()
    dim = dim.drop_duplicates(subset=["product_id"])

    return dim


# ============================================================
# DIM_SELLERS
# ============================================================

def create_dim_sellers(sellers):
    columns = [
        "seller_id",
        "seller_zip_code_prefix",
        "seller_city",
        "seller_state"
    ]

    dim = sellers[columns].copy()
    dim = dim.drop_duplicates(subset=["seller_id"])

    return dim


# ============================================================
# DIM_DATE
# ============================================================

def create_dim_date(orders):
    dates = (
        pd.to_datetime(
            orders["order_purchase_timestamp"],
            errors="coerce"
        )
        .dropna()
        .dt.normalize()
        .drop_duplicates()
    )

    dim = pd.DataFrame({"date": dates})

    dim["date_key"] = (
        dim["date"].dt.strftime("%Y%m%d").astype(int)
    )

    dim["year"] = dim["date"].dt.year
    dim["quarter"] = dim["date"].dt.quarter
    dim["month"] = dim["date"].dt.month
    dim["month_name"] = dim["date"].dt.month_name()
    dim["day"] = dim["date"].dt.day
    dim["day_of_week"] = dim["date"].dt.dayofweek
    dim["day_name"] = dim["date"].dt.day_name()
    dim["is_weekend"] = dim["day_of_week"].isin([5, 6])

    return dim.sort_values("date").reset_index(drop=True)


# ============================================================
# MAIN
# ============================================================

def main():
    customers, products, sellers, orders = load_data()

    dimensions = {
        "dim_customers": create_dim_customers(customers),
        "dim_products": create_dim_products(products),
        "dim_sellers": create_dim_sellers(sellers),
        "dim_date": create_dim_date(orders)
    }

    for name, df in dimensions.items():
        output = ANALYTICS / f"{name}.csv"

        df.to_csv(output, index=False)

        print(f"\n{name}")
        print(f"Records: {len(df):,}")
        print(f"Columns: {len(df.columns)}")
        print(f"Saved: {output}")

    print("\nAll dimensions created successfully.")


if __name__ == "__main__":
    main()
