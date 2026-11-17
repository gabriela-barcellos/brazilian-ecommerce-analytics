import pandas as pd

df = pd.read_csv("data/olist_order_reviews_dataset.csv")

print(f"Total de registros: {len(df):,}")
print(f"Order IDs duplicados: {df.duplicated('order_id').sum():,}")
print(
    "Duplicidades em review_id + order_id:",
    df.duplicated(["review_id", "order_id"]).sum()
)
print(
    "Duplicidades de linhas completas:",
    df.duplicated().sum()
)