
import pandas as pd

# ============================================================
# 1. LOAD DATASETS
# ============================================================

customers = pd.read_csv("data/olist_customers_dataset.csv")
orders = pd.read_csv("data/olist_orders_dataset.csv")
order_items = pd.read_csv("data/olist_order_items_dataset.csv")
products = pd.read_csv("data/olist_products_dataset.csv")
sellers = pd.read_csv("data/olist_sellers_dataset.csv")
payments = pd.read_csv("data/olist_order_payments_dataset.csv")
reviews = pd.read_csv("data/olist_order_reviews_dataset.csv")


# ============================================================
# 2. ORDERS → CUSTOMERS
# ============================================================

customer_ids = set(customers["customer_id"])
orders_without_customer = ~orders["customer_id"].isin(customer_ids)

print("\n--- Orders → Customers ---")
print(f"Total de pedidos: {len(orders):,}")
print(f"Pedidos com cliente correspondente: {(~orders_without_customer).sum():,}")
print(f"Pedidos sem cliente correspondente: {orders_without_customer.sum():,}")


# ============================================================
# 3. ORDERS → ORDER ITEMS
# ============================================================

item_order_ids = set(order_items["order_id"])
orders_without_items = ~orders["order_id"].isin(item_order_ids)

print("\n--- Orders → Order Items ---")
print(f"Total de pedidos: {len(orders):,}")
print(f"Pedidos com itens: {(~orders_without_items).sum():,}")
print(f"Pedidos sem itens: {orders_without_items.sum():,}")

print("\nStatus dos pedidos sem itens:")
print(orders.loc[orders_without_items, "order_status"].value_counts())

# Investigar pedidos sem itens que não sejam unavailable/canceled
other_status_orders = orders.loc[
    orders_without_items
    & ~orders["order_status"].isin(["unavailable", "canceled"])
]

print("\nPedidos sem itens em outros status:")
print(
    other_status_orders[
        ["order_id", "order_status", "order_approved_at",
         "order_delivered_carrier_date",
         "order_delivered_customer_date"]
    ].to_string(index=False)
)


# ============================================================
# 4. ORDER ITEMS → PRODUCTS
# ============================================================

product_ids = set(products["product_id"])
items_without_product = ~order_items["product_id"].isin(product_ids)

print("\n--- Order Items → Products ---")
print(f"Total de itens: {len(order_items):,}")
print(f"Itens com produto correspondente: {(~items_without_product).sum():,}")
print(f"Itens sem produto correspondente: {items_without_product.sum():,}")


# ============================================================
# 5. ORDER ITEMS → SELLERS
# ============================================================

seller_ids = set(sellers["seller_id"])
items_without_seller = ~order_items["seller_id"].isin(seller_ids)

print("\n--- Order Items → Sellers ---")
print(f"Total de itens: {len(order_items):,}")
print(f"Itens com vendedor correspondente: {(~items_without_seller).sum():,}")
print(f"Itens sem vendedor correspondente: {items_without_seller.sum():,}")


# ============================================================
# 6. ORDERS → PAYMENTS
# ============================================================

payment_order_ids = set(payments["order_id"])
order_ids = set(orders["order_id"])

orders_without_payment = ~orders["order_id"].isin(payment_order_ids)
payments_without_order = ~payments["order_id"].isin(order_ids)

print("\n--- Orders → Payments ---")
print(f"Total de pedidos: {len(orders):,}")
print(f"Pedidos sem pagamento: {orders_without_payment.sum():,}")
print(f"Total de registros de pagamento: {len(payments):,}")
print(f"Pagamentos sem pedido correspondente: {payments_without_order.sum():,}")


# ============================================================
# 7. ORDERS → REVIEWS
# ============================================================

review_order_ids = set(reviews["order_id"])

orders_without_review = ~orders["order_id"].isin(review_order_ids)
reviews_without_order = ~reviews["order_id"].isin(order_ids)

print("\n--- Orders → Reviews ---")
print(f"Total de pedidos: {len(orders):,}")
print(f"Pedidos sem avaliação: {orders_without_review.sum():,}")
print(f"Total de avaliações: {len(reviews):,}")
print(f"Avaliações sem pedido correspondente: {reviews_without_order.sum():,}")


# ============================================================
# 8. TEMPORAL CONSISTENCY
# ============================================================

date_columns = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date"
]

for column in date_columns:
    orders[column] = pd.to_datetime(orders[column], errors="coerce")

# Entregas anteriores à compra
delivered_before_purchase = (
    orders["order_delivered_customer_date"]
    < orders["order_purchase_timestamp"]
)

# Aprovações anteriores à compra
approved_before_purchase = (
    orders["order_approved_at"]
    < orders["order_purchase_timestamp"]
)

# Entregas anteriores à aprovação
delivered_before_approval = (
    orders["order_delivered_customer_date"]
    < orders["order_approved_at"]
)

print("\n--- Consistência Temporal ---")
print(f"Entregas anteriores à compra: {delivered_before_purchase.sum():,}")
print(f"Aprovações anteriores à compra: {approved_before_purchase.sum():,}")
print(f"Entregas anteriores à aprovação: {delivered_before_approval.sum():,}")

print("\nDetalhes das entregas anteriores à aprovação:")
print(
    orders.loc[
        delivered_before_approval,
        [
            "order_id",
            "order_status",
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_customer_date"
        ]
    ].to_string(index=False)
)


# ============================================================
# 9. DELIVERIES VS ESTIMATED DATE
# ============================================================

delivered_after_estimated = (
    orders["order_delivered_customer_date"]
    > orders["order_estimated_delivery_date"]
)

delivered_on_time = (
    orders["order_delivered_customer_date"]
    <= orders["order_estimated_delivery_date"]
)

print("\n--- Entregas vs. Prazo Estimado ---")
print(f"Entregas após o prazo: {delivered_after_estimated.sum():,}")
print(f"Entregas dentro do prazo: {delivered_on_time.sum():,}")


# ============================================================
# 10. CANCELED ORDERS WITH DELIVERY DATES
# ============================================================

canceled_orders = orders[
    orders["order_status"] == "canceled"
]

canceled_with_delivery = canceled_orders[
    canceled_orders["order_delivered_customer_date"].notna()
]

canceled_with_carrier = canceled_orders[
    canceled_orders["order_delivered_carrier_date"].notna()
]

print("\n--- Cancelados com Datas de Entrega ---")
print(f"Pedidos cancelados: {len(canceled_orders):,}")
print(f"Cancelados com entrega ao cliente: {len(canceled_with_delivery):,}")
print(f"Cancelados com entrega à transportadora: {len(canceled_with_carrier):,}")

print("\nDetalhes dos cancelados com entrega ao cliente:")
print(
    canceled_with_delivery[
        [
            "order_id",
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date"
        ]
    ].to_string(index=False)
)
