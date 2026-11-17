
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

EXPECTED_ROWS = {
    "customers": 99441,
    "geolocation": 1000163,
    "order_items": 112650,
    "order_payments": 103886,
    "order_reviews": 99224,
    "orders": 99441,
    "products": 32951,
    "sellers": 3095,
    "category_translation": 71,
}

def validate_pipeline():

    print("=" * 60)
    print("PIPELINE VALIDATION")
    print("=" * 60)

    failures = []

    for name, expected_rows in EXPECTED_ROWS.items():

        raw_file = RAW_DIR / f"olist_{name}_dataset.csv"
        if name == "category_translation":
            raw_file = RAW_DIR / "product_category_name_translation.csv"

        processed_file = PROCESSED_DIR / f"{name}.csv"

        if not raw_file.exists():
            print(f"{name}: RAW FILE MISSING")
            failures.append(name)
            continue

        if not processed_file.exists():
            print(f"{name}: PROCESSED FILE MISSING")
            failures.append(name)
            continue

        df = pd.read_csv(processed_file)
        actual_rows = len(df)

        passed = actual_rows == expected_rows

        print(
            f"{name}: {'PASS' if passed else 'FAIL'} | "
            f"Rows: {actual_rows:,} | Expected: {expected_rows:,}"
        )

        if not passed:
            failures.append(name)

    print("\n" + "-" * 60)
    print(f"Datasets checked: {len(EXPECTED_ROWS)}")
    print(f"Failures: {len(failures)}")
    print(
        "PIPELINE STATUS:",
        "PASS" if not failures else "REVIEW"
    )
    print("=" * 60)

if __name__ == "__main__":
    validate_pipeline()
