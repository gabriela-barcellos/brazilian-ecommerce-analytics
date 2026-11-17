
from pathlib import Path
import pandas as pd

# ============================================================
# ANALYTICS METRICS VALIDATION
# Brazilian E-commerce (Olist)
# ============================================================

ROOT = Path(__file__).resolve().parent.parent
ANALYTICS = ROOT / "data" / "analytics"
RAW = ROOT / "data" / "raw"


# ============================================================
# LOAD DATA
# ============================================================

def load_data():
    return {
        "fact": pd.read_csv(ANALYTICS / "fact_sales.csv"),
        "monthly": pd.read_csv(
            ANALYTICS / "monthly_sales_metrics.csv"
        ),
        "products": pd.read_csv(
            ANALYTICS / "product_metrics.csv"
        ),
        "categories": pd.read_csv(
            ANALYTICS / "category_metrics.csv"
        ),
        "states": pd.read_csv(
            ANALYTICS / "state_metrics.csv"
        ),
        "payments": pd.read_csv(
            ANALYTICS / "payment_metrics.csv"
        ),
        "customers": pd.read_csv(
            ANALYTICS / "customer_metrics.csv"
        ),
        "kpis": pd.read_csv(
            ANALYTICS / "general_kpis.csv"
        ),
        "raw_payments": pd.read_csv(
            RAW / "olist_order_payments_dataset.csv"
        )
    }


# ============================================================
# VALIDATION HELPERS
# ============================================================

def close_values(a, b, tolerance=0.01):
    return abs(a - b) <= tolerance


def validate_metrics(data):
    fact = data["fact"]
    monthly = data["monthly"]
    products = data["products"]
    categories = data["categories"]
    states = data["states"]
    payments = data["payments"]
    customers = data["customers"]
    kpis = data["kpis"]
    raw_payments = data["raw_payments"]

    results = []

    # --------------------------------------------------------
    # GENERAL KPIS
    # --------------------------------------------------------

    total_revenue = fact["item_revenue"].sum()
    total_orders = fact["order_id"].nunique()
    total_customers = fact["customer_unique_id"].nunique()
    total_units = len(fact)

    results.append((
        "KPI Revenue",
        close_values(kpis.loc[0, "Revenue"], total_revenue)
    ))

    results.append((
        "KPI Orders",
        kpis.loc[0, "Orders"] == total_orders
    ))

    results.append((
        "KPI Customers",
        kpis.loc[0, "Customers"] == total_customers
    ))

    results.append((
        "KPI Units Sold",
        kpis.loc[0, "UnitsSold"] == total_units
    ))

    expected_ticket = total_revenue / total_orders

    results.append((
        "KPI Average Ticket",
        close_values(
            kpis.loc[0, "AverageTicket"],
            expected_ticket
        )
    ))

    # --------------------------------------------------------
    # MONTHLY SALES
    # --------------------------------------------------------

    results.append((
        "Monthly Revenue",
        close_values(
            monthly["Revenue"].sum(),
            total_revenue
        )
    ))

    results.append((
        "Monthly Orders",
        monthly["Orders"].sum() >= total_orders
    ))

    # --------------------------------------------------------
    # PRODUCTS AND CATEGORIES
    # --------------------------------------------------------

    results.append((
        "Product Revenue",
        close_values(
            products["Revenue"].sum(),
            total_revenue
        )
    ))

    results.append((
        "Category Revenue",
        close_values(
            categories["Revenue"].sum(),
            total_revenue
        )
    ))

    # --------------------------------------------------------
    # STATES
    # --------------------------------------------------------

    results.append((
        "State Revenue",
        close_values(
            states["Revenue"].sum(),
            total_revenue
        )
    ))

    # --------------------------------------------------------
    # CUSTOMERS
    # --------------------------------------------------------

    results.append((
        "Customer Revenue",
        close_values(
            customers["Revenue"].sum(),
            total_revenue
        )
    ))

    results.append((
        "Customer Count",
        customers["customer_unique_id"].nunique()
        == total_customers
    ))

    # --------------------------------------------------------
    # PAYMENTS
    # --------------------------------------------------------

    expected_payment_value = raw_payments["payment_value"].sum()

    results.append((
        "Payment Value",
        close_values(
            payments["PaymentValue"].sum(),
            expected_payment_value
        )
    ))

    results.append((
        "Payment Orders",
        payments["Orders"].sum()
        >= raw_payments["order_id"].nunique()
    ))

    return results


# ============================================================
# REPORT
# ============================================================

def main():
    data = load_data()
    results = validate_metrics(data)

    passed = 0
    failed = 0

    print("\n" + "=" * 60)
    print("ANALYTICS METRICS - VALIDATION")
    print("=" * 60)

    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status:<6} | {name}")

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
        print("All analytics metrics validations passed.")
    else:
        print("Attention: validation failures detected.")


if __name__ == "__main__":
    main()
