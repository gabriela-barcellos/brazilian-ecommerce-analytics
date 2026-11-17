
from pathlib import Path
import pandas as pd

# ============================================================
# PROJECT CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# DATASETS
# ============================================================

DATASETS = {
    "customers": "olist_customers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}

# ============================================================
# DATETIME COLUMNS
# ============================================================

DATETIME_COLUMNS = {
    "orders": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "order_reviews": [
        "review_creation_date",
        "review_answer_timestamp",
    ],
}

# ============================================================
# TRANSFORMATION
# ============================================================

def transform_data():

    print("=" * 60)
    print("BRAZILIAN E-COMMERCE | DATA TRANSFORMATION")
    print("=" * 60)

    transformed_datasets = {}

    for dataset_name, filename in DATASETS.items():

        raw_path = RAW_DIR / filename

        if not raw_path.exists():
            raise FileNotFoundError(
                f"Arquivo não encontrado: {raw_path}"
            )

        df = pd.read_csv(raw_path)

        # Standardize column names
        df.columns = (
            df.columns
            .str.strip()
            .str.lower()
            .str.replace(" ", "_")
        )

        # Convert datetime columns
        for column in DATETIME_COLUMNS.get(dataset_name, []):

            if column in df.columns:
                df[column] = pd.to_datetime(
                    df[column],
                    errors="coerce"
                )

        # Save transformed dataset
        output_path = (
            PROCESSED_DIR / f"{dataset_name}.csv"
        )

        df.to_csv(output_path, index=False)

        transformed_datasets[dataset_name] = df

        print(f"\nDataset: {dataset_name}")
        print(f"Rows: {len(df):,}")
        print(f"Columns: {len(df.columns)}")
        print(f"Saved: {output_path.name}")

    print("\n" + "=" * 60)
    print("TRANSFORMATION COMPLETED SUCCESSFULLY")
    print(f"Datasets processed: {len(transformed_datasets)}")
    print("=" * 60)

    return transformed_datasets


# ============================================================
# EXECUTION
# ============================================================

if __name__ == "__main__":
    data = transform_data()
