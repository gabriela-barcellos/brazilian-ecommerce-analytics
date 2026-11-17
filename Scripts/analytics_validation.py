
from pathlib import Path
import pandas as pd

# ============================================================
# ANALYTICS VALIDATION
# Brazilian E-commerce (Olist)
# ============================================================

ROOT = Path(__file__).resolve().parent.parent
ANALYTICS = ROOT / "data" / "analytics"


def load_data():
    return {
        "fact_sales": pd.read_csv(ANALYTICS / "fact_sales.csv"),
        "dim_customers": pd.read_csv(ANALYTICS / "dim_customers.csv"),
        "dim_products": pd.read_csv(ANALYTICS / "dim_products.csv"),
        "dim_sellers": pd.read_csv(ANALYTICS / "dim_sellers.csv"),
        "dim_date": pd.read_csv(ANALYTICS / "dim_date.csv"),
    }


def check_primary_key(df, columns):
    return not df.duplicated(subset=columns).any()


def check_null_keys(df, columns):
    return not df[columns].isnull().any().any()


def check_foreign_key(fact, fact_column, dimension, dimension_column):
    fact_values = set(fact[fact_column].dropna())
    dimension_values = set(dimension[dimension_column].dropna())

    return fact_values.issubset(dimension_values)


def run_validation(data):
    fact = data["fact_sales"]
    customers = data["dim_customers"]
    products = data["dim_products"]
    sellers = data["dim_sellers"]
    dates = data["dim_date"]

    results = []

    # --------------------------------------------------------
    # FACT SALES
    # --------------------------------------------------------

    results.append((
        "Fact Sales - Primary Key",
        check_primary_key(fact, ["order_id", "order_item_id"])
    ))

    results.append((
        "Fact Sales - Null Keys",
        check_null_keys(fact, ["order_id", "order_item_id"])
    ))

    # --------------------------------------------------------
    # DIMENSIONS - PRIMARY KEYS
    # --------------------------------------------------------

    results.append((
        "Dim Customers - Primary Key",
        check_primary_key(customers, ["customer_id"])
    ))

    results.append((
        "Dim Products - Primary Key",
        check_primary_key(products, ["product_id"])
    ))

    results.append((
        "Dim Sellers - Primary Key",
        check_primary_key(sellers, ["seller_id"])
    ))

    results.append((
        "Dim Date - Primary Key",
        check_primary_key(dates, ["date_key"])
    ))

    # --------------------------------------------------------
    # DIMENSIONS - NULL KEYS
    # --------------------------------------------------------

    results.append((
        "Dim Customers - Null Keys",
        check_null_keys(customers, ["customer_id"])
    ))

    results.append((
        "Dim Products - Null Keys",
        check_null_keys(products, ["product_id"])
    ))

    results.append((
        "Dim Sellers - Null Keys",
        check_null_keys(sellers, ["seller_id"])
    ))

    results.append((
        "Dim Date - Null Keys",
        check_null_keys(dates, ["date_key"])
    ))

    # --------------------------------------------------------
    # FOREIGN KEYS
    # --------------------------------------------------------

    results.append((
        "FK Fact -> Customers",
        check_foreign_key(
            fact, "customer_id",
            customers, "customer_id"
        )
    ))

    results.append((
        "FK Fact -> Products",
        check_foreign_key(
            fact, "product_id",
            products, "product_id"
        )
    ))

    results.append((
        "FK Fact -> Sellers",
        check_foreign_key(
            fact, "seller_id",
            sellers, "seller_id"
        )
    ))

    # --------------------------------------------------------
    # DATE INTEGRITY
    # --------------------------------------------------------

    fact_dates = set(
        pd.to_datetime(fact["purchase_date"], errors="coerce")
        .dropna()
        .dt.strftime("%Y-%m-%d")
    )

    dimension_dates = set(
        pd.to_datetime(dates["date"], errors="coerce")
        .dropna()
        .dt.strftime("%Y-%m-%d")
    )

    results.append((
        "FK Fact -> Date",
        fact_dates.issubset(dimension_dates)
    ))

    # --------------------------------------------------------
    # REPORT
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("ANALYTICS DATA WAREHOUSE - VALIDATION")
    print("=" * 60)

    passed = 0
    failed = 0

    for test_name, result in results:
        status = "PASS" if result else "FAIL"

        print(f"{status:<6} | {test_name}")

        if result:
            passed += 1
        else:
            failed += 1

    print("-" * 60)
    print(f"Total: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print("=" * 60)

    if failed == 0:
        print("All analytics validations passed.")
    else:
        print("Attention: validation failures detected.")


def main():
    data = load_data()
    run_validation(data)


if __name__ == "__main__":
    main()
