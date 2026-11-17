
from pathlib import Path
import pandas as pd

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"

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


def ingest_data():
    datasets = {}

    print("=" * 60)
    print("BRAZILIAN E-COMMERCE | DATA INGESTION")
    print("=" * 60)

    for name, filename in DATASETS.items():
        file_path = RAW_DIR / filename

        if not file_path.exists():
            raise FileNotFoundError(
                f"Arquivo não encontrado: {file_path}"
            )

        df = pd.read_csv(file_path)

        datasets[name] = df

        print(f"\nDataset: {name}")
        print(f"Arquivo: {filename}")
        print(f"Linhas: {len(df):,}")
        print(f"Colunas: {len(df.columns)}")

    print("\n" + "=" * 60)
    print("INGESTION COMPLETED SUCCESSFULLY")
    print(f"Datasets carregados: {len(datasets)}")
    print("=" * 60)

    return datasets


if __name__ == "__main__":
    data = ingest_data()
