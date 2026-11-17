from pathlib import Path
import pandas as pd

DATA_DIR = Path("data")

KEYS = {
    "olist_customers_dataset.csv": ["customer_id"],
    "olist_orders_dataset.csv": ["order_id"],
    "olist_order_items_dataset.csv": ["order_id", "order_item_id"],
    "olist_order_payments_dataset.csv": ["order_id", "payment_sequential"],
    "olist_order_reviews_dataset.csv": ["review_id"],
    "olist_products_dataset.csv": ["product_id"],
    "olist_sellers_dataset.csv": ["seller_id"],
}

for file_name, columns in KEYS.items():
    df = pd.read_csv(DATA_DIR / file_name)

    duplicates = df.duplicated(subset=columns).sum()

    print(f"\nTabela: {file_name}")
    print(f"Chave candidata: {columns}")
    print(f"Registros: {len(df):,}")
    print(f"Duplicidades na chave: {duplicates:,}")