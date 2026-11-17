
import pandas as pd

# ============================================================
# 1. LOAD DATA
# ============================================================

orders = pd.read_csv("data/olist_orders_dataset.csv")
items = pd.read_csv("data/olist_order_items_dataset.csv")
payments = pd.read_csv("data/olist_order_payments_dataset.csv")


# ============================================================
# 2. CARDINALITY
# ============================================================

print("\n--- Cardinalidade ---")

print("Pedidos:", orders["order_id"].nunique())
print("Itens:", len(items))
print("Pagamentos:", len(payments))

print("\nItens por pedido:")
print(items.groupby("order_id").size().describe())

print("\nPagamentos por pedido:")
print(payments.groupby("order_id").size().describe())


# ============================================================
# 3. REVENUE AT ITEM LEVEL
# ============================================================

items["item_revenue"] = items["price"]

revenue_items = items["item_revenue"].sum()

print("\n--- Receita na tabela de itens ---")
print(f"Receita: R$ {revenue_items:,.2f}")


# ============================================================
# 4. REVENUE AT PAYMENT LEVEL
# ============================================================

revenue_payments = payments["payment_value"].sum()

print("\n--- Receita na tabela de pagamentos ---")
print(f"Pagamentos: R$ {revenue_payments:,.2f}")


# ============================================================
# 5. JOIN ITEMS × PAYMENTS
# ============================================================

joined = items.merge(
    payments,
    on="order_id",
    how="inner"
)

joined_revenue = joined["price"].sum()

print("\n--- Impacto do JOIN ---")
print(f"Linhas antes: {len(items):,}")
print(f"Linhas após JOIN: {len(joined):,}")
print(f"Receita original dos itens: R$ {revenue_items:,.2f}")
print(f"Receita após JOIN: R$ {joined_revenue:,.2f}")

print(
    "\nMultiplicação da receita:",
    round(joined_revenue / revenue_items, 2),
    "vezes"
)


# ============================================================
# 6. CORRECT AGGREGATION BEFORE JOIN
# ============================================================

items_per_order = (
    items.groupby("order_id", as_index=False)
    .agg(item_revenue=("price", "sum"))
)

payments_per_order = (
    payments.groupby("order_id", as_index=False)
    .agg(payment_total=("payment_value", "sum"))
)

safe_join = items_per_order.merge(
    payments_per_order,
    on="order_id",
    how="inner"
)

print("\n--- JOIN após agregação ---")
print(f"Pedidos combinados: {len(safe_join):,}")
print(f"Receita dos itens: R$ {safe_join['item_revenue'].sum():,.2f}")
print(f"Total de pagamentos: R$ {safe_join['payment_total'].sum():,.2f}")
