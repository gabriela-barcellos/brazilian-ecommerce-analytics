from pathlib import Path
import pandas as pd

DATA_DIR = Path("data")
OUTPUT_DIR = Path("reports")

OUTPUT_DIR.mkdir(exist_ok=True)

inventory = []

for file in sorted(DATA_DIR.glob("*.csv")):
    df = pd.read_csv(file)

    inventory.append({
        "file_name": file.name,
        "rows": len(df),
        "columns": len(df.columns),
        "size_kb": round(file.stat().st_size / 1024, 2)
    })

    print(f"{file.name} | {len(df):,} linhas | {len(df.columns)} colunas")

inventory_df = pd.DataFrame(inventory)

inventory_df.to_csv(
    OUTPUT_DIR / "dataset_inventory.csv",
    index=False,
    encoding="utf-8"
)

print("\nInventário salvo em reports/dataset_inventory.csv")