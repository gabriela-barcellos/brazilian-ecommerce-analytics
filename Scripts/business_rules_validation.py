
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "processed"


def validate_business_rules():

    print("=" * 60)
    print("BUSINESS RULES VALIDATION")
    print("=" * 60)

    # Order items
    items = pd.read_csv(DATA_DIR / "order_items.csv")

    checks = {
        "Order item ID > 0": (items["order_item_id"] > 0).all(),
        "Price >= 0": (items["price"] >= 0).all(),
        "Freight value >= 0": (items["freight_value"] >= 0).all(),
    }

    # Payments
    payments = pd.read_csv(DATA_DIR / "order_payments.csv")

    checks.update({
        "Payment value >= 0": (payments["payment_value"] >= 0).all(),
        "Payment installments >= 1": (
            payments["payment_installments"] >= 1
        ).all(),
    })

    # Reviews
    reviews = pd.read_csv(DATA_DIR / "order_reviews.csv")

    checks["Review score between 1 and 5"] = (
        reviews["review_score"].between(1, 5).all()
    )

    # Products
    products = pd.read_csv(DATA_DIR / "products.csv")

    checks["Product weight >= 0"] = (
        products["product_weight_g"].dropna() >= 0
    ).all()

    # Orders
    orders = pd.read_csv(DATA_DIR / "orders.csv")

    checks["Valid order statuses"] = orders["order_status"].isin([
        "delivered", "shipped", "canceled", "unavailable",
        "invoiced", "processing", "created", "approved"
    ]).all()

    # Results
    failed = []

    for rule, passed in checks.items():
        status = "PASS" if passed else "FAIL"
        print(f"{rule}: {status}")

        if not passed:
            failed.append(rule)

    print("\n" + "-" * 60)
    print(f"Rules checked: {len(checks)}")
    print(f"Passed: {len(checks) - len(failed)}")
    print(f"Failed: {len(failed)}")

    if failed:
        print("\nRules requiring investigation:")
        for rule in failed:
            print(f"- {rule}")

    print("\nBUSINESS RULES VALIDATION COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    validate_business_rules()
