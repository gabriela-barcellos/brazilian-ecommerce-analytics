
from pathlib import Path
import pandas as pd

# ============================================================
# ANALYTICS METRICS
# Brazilian E-commerce (Olist)
# ============================================================

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"
RAW = ROOT / "data" / "raw"
ANALYTICS = ROOT / "data" / "analytics"

ANALYTICS.mkdir(parents=True, exist_ok=True)


# ============================================================
# LOAD DATA
# ============================================================

def load_data():
    fact = pd.read_csv(
        ANALYTICS / "fact_sales.csv",
        parse_dates=["order_purchase_timestamp"]
    )

    payments = pd.read_csv(
        RAW / "olist_order_payments_dataset.csv"
    )

    return fact, payments


# ============================================================
# SALES METRICS
# ============================================================

def create_sales_metrics(fact):
    sales = fact.copy()

    sales["purchase_year_month"] = (
        sales["order_purchase_timestamp"]
        .dt.to_period("M")
        .astype(str)
    )

    monthly = sales.groupby("purchase_year_month").agg(
        Revenue=("item_revenue", "sum"),
        FreightRevenue=("freight_value", "sum"),
        UnitsSold=("order_item_id", "count"),
        Orders=("order_id", "nunique"),
        Customers=("customer_unique_id", "nunique")
    ).reset_index()

    monthly["AverageTicket"] = (
        monthly["Revenue"] / monthly["Orders"]
    )

    monthly["RevenueGrowth"] = (
        monthly["Revenue"].pct_change() * 100
    )

    return monthly


# ============================================================
# PRODUCT METRICS
# ============================================================

def create_product_metrics(fact):
    products = fact.groupby(
        ["product_id", "product_category_name"],
        dropna=False
    ).agg(
        Revenue=("item_revenue", "sum"),
        UnitsSold=("order_item_id", "count"),
        Orders=("order_id", "nunique")
    ).reset_index()

    categories = fact.groupby(
        "product_category_name",
        dropna=False
    ).agg(
        Revenue=("item_revenue", "sum"),
        UnitsSold=("order_item_id", "count"),
        Orders=("order_id", "nunique")
    ).reset_index()

    categories = categories.sort_values(
        "Revenue", ascending=False
    )

    return products, categories


# ============================================================
# GEOGRAPHIC METRICS
# ============================================================

def create_state_metrics(fact):
    states = fact.groupby("customer_state").agg(
        Revenue=("item_revenue", "sum"),
        Orders=("order_id", "nunique"),
        Customers=("customer_unique_id", "nunique"),
        UnitsSold=("order_item_id", "count")
    ).reset_index()

    states["AverageTicket"] = (
        states["Revenue"] / states["Orders"]
    )

    return states.sort_values("Revenue", ascending=False)


# ============================================================
# PAYMENT METRICS
# ============================================================

def create_payment_metrics(payments):
    payment_metrics = payments.groupby(
        "payment_type",
        dropna=False
    ).agg(
        PaymentValue=("payment_value", "sum"),
        PaymentCount=("payment_sequential", "count"),
        Orders=("order_id", "nunique")
    ).reset_index()

    return payment_metrics.sort_values(
        "PaymentValue", ascending=False
    )


# ============================================================
# CUSTOMER METRICS
# ============================================================

def create_customer_metrics(fact):
    customers = fact.groupby(
        "customer_unique_id"
    ).agg(
        Revenue=("item_revenue", "sum"),
        Orders=("order_id", "nunique"),
        UnitsSold=("order_item_id", "count")
    ).reset_index()

    customers["AverageTicket"] = (
        customers["Revenue"] / customers["Orders"]
    )

    return customers.sort_values(
        "Revenue", ascending=False
    )


# ============================================================
# GENERAL KPIS
# ============================================================

def create_general_kpis(fact):
    revenue = fact["item_revenue"].sum()
    orders = fact["order_id"].nunique()
    customers = fact["customer_unique_id"].nunique()
    units = len(fact)

    return pd.DataFrame([{
        "Revenue": revenue,
        "Orders": orders,
        "AverageTicket": revenue / orders if orders else 0,
        "Customers": customers,
        "UnitsSold": units
    }])


# ============================================================
# SAVE OUTPUTS
# ============================================================

def save_metrics(metrics):
    for name, df in metrics.items():
        output = ANALYTICS / f"{name}.csv"
        df.to_csv(output, index=False)

        print(f"{name}: {len(df):,} registros")
        print(f"Arquivo: {output}")


# ============================================================
# MAIN
# ============================================================

def main():
    fact, payments = load_data()

    products, categories = create_product_metrics(fact)

    metrics = {
        "monthly_sales_metrics": create_sales_metrics(fact),
        "product_metrics": products,
        "category_metrics": categories,
        "state_metrics": create_state_metrics(fact),
        "payment_metrics": create_payment_metrics(payments),
        "customer_metrics": create_customer_metrics(fact),
        "general_kpis": create_general_kpis(fact)
    }

    save_metrics(metrics)

    print("\nAnalytics metrics generated successfully.")


if __name__ == "__main__":
    main()
