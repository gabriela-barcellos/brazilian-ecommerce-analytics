from pathlib import Path
import pandas as pd

DATA_DIR = Path("data")
OUTPUT_DIR = Path("reports")

OUTPUT_DIR.mkdir(exist_ok=True)

schema_data = []

for file in sorted(DATA_DIR.glob("*.csv")):
    df = pd.read_csv(file)

    print(f"\n{'=' * 60}")
    print(f"TABELA: {file.name}")
    print(f"{'=' * 60}")

    for column in df.columns:
        dtype = str(df[column].dtype)
        null_count = int(df[column].isna().sum())

        schema_data.append({
            "table": file.name,
            "column": column,
            "dtype": dtype,
            "null_count": null_count
        })

        print(
            f"{column:<40} "
            f"Tipo: {dtype:<12} "
            f"Nulos: {null_count:,}"
        )

schema_df = pd.DataFrame(schema_data)

schema_df.to_csv(
    OUTPUT_DIR / "schema_inspection.csv",
    index=False,
    encoding="utf-8"
)

print("\nSchema salvo em reports/schema_inspection.csv")