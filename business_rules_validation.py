
import pandas as pd

# ============================================================
# 1. LOAD DATASETS
# ============================================================

items = pd.read_csv("data/olist_order_items_dataset.csv")
payments = pd.read_csv("data/olist_order_payments_dataset.csv")
reviews = pd.read_csv("data/olist_order_reviews_dataset.csv")
products = pd.read_csv("data/olist_products_dataset.csv")
orders = pd.read_csv("data/olist_orders_dataset.csv")


# ============================================================
# 2. ORDER ITEMS: BUSINESS RULES
# ============================================================

print("\n--- Order Items: Regras de Negócio ---")

print("order_item_id <= 0:", (items["order_item_id"] <= 0).sum())
print("Preço negativo:", (items["price"] < 0).sum())
print("Frete negativo:", (items["freight_value"] < 0).sum())
print("Preço zero:", (items["price"] == 0).sum())
print("Frete zero:", (items["freight_value"] == 0).sum())

print("\nEstatísticas de preço:")
print(items["price"].describe())

print("\nEstatísticas de frete:")
print(items["freight_value"].describe())


# ============================================================
# 3. PAYMENTS: BUSINESS RULES
# ============================================================

print("\n--- Payments: Regras de Negócio ---")

print("Pagamento negativo:", (payments["payment_value"] < 0).sum())
print("Pagamento zero:", (payments["payment_value"] == 0).sum())
print("Parcelas menores que 1:", (payments["payment_installments"] < 1).sum())

print("\nTipos de pagamento:")
print(payments["payment_type"].value_counts(dropna=False))

print("\nEstatísticas de pagamento:")
print(payments["payment_value"].describe())

print("\nEstatísticas de parcelas:")
print(payments["payment_installments"].describe())


# ============================================================
# 4. INVESTIGATION: ZERO PAYMENTS
# ============================================================

zero_payments = payments.loc[payments["payment_value"] == 0]

print("\n--- Investigação: Pagamentos Zerados ---")
print(f"Quantidade: {len(zero_payments)}")

print(
    zero_payments[
        [
            "order_id",
            "payment_sequential",
            "payment_type",
            "payment_installments",
            "payment_value"
        ]
    ].to_string(index=False)
)


# ============================================================
# 5. INVESTIGATION: INSTALLMENTS < 1
# ============================================================

invalid_installments = payments.loc[
    payments["payment_installments"] < 1
]

print("\n--- Investigação: Parcelas Menores que 1 ---")
print(f"Quantidade: {len(invalid_installments)}")

print(
    invalid_installments[
        [
            "order_id",
            "payment_sequential",
            "payment_type",
            "payment_installments",
            "payment_value"
        ]
    ].to_string(index=False)
)


# ============================================================
# 6. REVIEWS: SCORE VALIDATION
# ============================================================

print("\n--- Reviews: Regras de Negócio ---")

invalid_scores = ~reviews["review_score"].between(1, 5)

print("Scores inválidos:", invalid_scores.sum())

print("\nDistribuição de scores:")
print(reviews["review_score"].value_counts().sort_index())


# ============================================================
# 7. PRODUCTS: PHYSICAL ATTRIBUTES
# ============================================================

print("\n--- Products: Regras de Negócio ---")

physical_columns = [
    "product_weight_g",
    "product_length_cm",
    "product_height_cm",
    "product_width_cm"
]

for column in physical_columns:
    print(f"{column} negativos:", (products[column] < 0).sum())
    print(f"{column} iguais a zero:", (products[column] == 0).sum())

print(
    "\nProdutos sem categoria:",
    products["product_category_name"].isna().sum()
)


# ============================================================
# 8. ORDERS: STATUS VALIDATION
# ============================================================

print("\n--- Orders: Status ---")

print("\nDistribuição de status:")
print(orders["order_status"].value_counts(dropna=False))

valid_statuses = [
    "created",
    "approved",
    "invoiced",
    "processing",
    "shipped",
    "delivered",
    "unavailable",
    "canceled"
]

invalid_status = ~orders["order_status"].isin(valid_statuses)

print("Status fora da lista esperada:", invalid_status.sum())


# ============================================================
# 9. PAYMENT TYPES VALIDATION
# ============================================================

valid_payment_types = [
    "credit_card",
    "boleto",
    "voucher",
    "debit_card",
    "not_defined"
]

invalid_payment_types = ~payments["payment_type"].isin(
    valid_payment_types
)

print("\n--- Tipos de Pagamento ---")
print("Tipos fora da lista esperada:", invalid_payment_types.sum())


# ============================================================
# 10. BUSINESS KEYS
# ============================================================

print("\n--- Chaves de Negócio ---")

print(
    "Duplicatas order_id + order_item_id:",
    items.duplicated(["order_id", "order_item_id"]).sum()
)

print(
    "Duplicatas order_id + payment_sequential:",
    payments.duplicated(["order_id", "payment_sequential"]).sum()
)


# ============================================================
# 11. MISSING VALUES
# ============================================================

print("\n--- Valores Ausentes ---")

datasets = {
    "Order Items": items,
    "Payments": payments,
    "Reviews": reviews,
    "Products": products,
    "Orders": orders
}

for name, df in datasets.items():
    print(f"\n{name}:")
    print(df.isna().sum())
