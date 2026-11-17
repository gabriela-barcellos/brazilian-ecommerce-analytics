
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"

DATASETS = {
    "customers": ("customers.csv", ["customer_id"]),
    "orders": ("orders.csv", ["order_id"]),
    "order_items": ("order_items.csv", ["order_id", "order_item_id"]),
    "order_payments": ("order_payments.csv", ["order_id", "payment_sequential"]),
    "products": ("products.csv", ["product_id"]),
    "sellers": ("sellers.csv", ["seller_id"]),
}

def validate_data():

    print("=" * 60)
    print("DATA QUALITY VALIDATION")
    print("=" * 60)

    for name, (filename, keys) in DATASETS.items():

        path = PROCESSED_DIR / filename
        df = pd.read_csv(path)

        duplicates = df.duplicated(subset=keys).sum()
        null_keys = df[keys].isnull().any(axis=1).sum()

        print(f"\nDataset: {name}")
        print(f"Rows: {len(df):,}")
        print(f"Null key records: {null_keys:,}")
        print(f"Duplicate keys: {duplicates:,}")

        if duplicates == 0 and null_keys == 0:
            print("Status: PASS")
        else:
            print("Status: REVIEW")

    # Referential integrity
    customers = pd.read_csv(PROCESSED_DIR / "customers.csv")
    orders = pd.read_csv(PROCESSED_DIR / "orders.csv")
    products = pd.read_csv(PROCESSED_DIR / "products.csv")
    sellers = pd.read_csv(PROCESSED_DIR / "sellers.csv")
    items = pd.read_csv(PROCESSED_DIR / "order_items.csv")

    checks = {
        "orders.customer_id": (
            orders["customer_id"].isin(customers["customer_id"]).all()
        ),
        "items.product_id": (
            items["product_id"].isin(products["product_id"]).all()
        ),
        "items.seller_id": (
            items["seller_id"].isin(sellers["seller_id"]).all()
        ),
    }

    print("\n" + "-" * 60)
    print("REFERENTIAL INTEGRITY")

    for relationship, passed in checks.items():
        print(f"{relationship}: {'PASS' if passed else 'FAIL'}")

    print("\nVALIDATION COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    validate_data()
