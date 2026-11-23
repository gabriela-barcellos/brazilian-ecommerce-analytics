"""
BRAZILIAN E-COMMERCE | QUALITY CHECKS

Verificações automáticas sobre Bronze, Silver e Gold no PostgreSQL.
Reúne e substitui, para o banco, a lógica dos scripts em pandas:
  pipeline_validation.py, data_quality_validation.py, key_validation.py,
  relationship_validation.py, business_rules_validation.py,
  analytics_validation.py e analytics_metrics_validation.py.

Cada verificação é uma consulta que devolve UM valor, comparado com o
valor esperado (texto exato).
  critical -> se falhar, a execução é marcada 'failed' e o script sai com erro
  warning  -> registra a ocorrência conhecida (baseline do
              reports/data_quality_report.md). Se o número mudar, aparece
              como ALERTA, mas não interrompe o pipeline.

Resultados em control.quality_results (uma linha por verificação).
"""

from db import get_connection

PIPELINE_NAME = "quality_checks"

# ============================================================
# CHECKS: (camada, severidade, nome, sql, esperado)
# ============================================================

BRONZE_EXPECTED_ROWS = {  # mesmo dicionário do pipeline_validation.py
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

CHECKS = []

# ---------- BRONZE: contagem da origem ----------
for table, rows in BRONZE_EXPECTED_ROWS.items():
    CHECKS.append(("bronze", "critical", f"linhas bronze.{table}",
                   f"SELECT COUNT(*) FROM bronze.{table}", str(rows)))

# ---------- SILVER: nenhuma linha perdida ----------
for table in BRONZE_EXPECTED_ROWS:
    CHECKS.append(("silver", "critical", f"silver.{table} = bronze.{table}",
                   f"SELECT (SELECT COUNT(*) FROM silver.{table}) - (SELECT COUNT(*) FROM bronze.{table})",
                   "0"))

CHECKS += [
    # ---------- SILVER: chaves e integridade (data_quality / relationship) ----------
    ("silver", "critical", "chave duplicada order_items (order_id, order_item_id)",
     "SELECT COUNT(*) - COUNT(DISTINCT (order_id, order_item_id)) FROM silver.order_items", "0"),
    ("silver", "critical", "chave duplicada order_payments (order_id, payment_sequential)",
     "SELECT COUNT(*) - COUNT(DISTINCT (order_id, payment_sequential)) FROM silver.order_payments", "0"),
    ("silver", "critical", "chave duplicada order_reviews (review_id, order_id)",
     "SELECT COUNT(*) - COUNT(DISTINCT (review_id, order_id)) FROM silver.order_reviews", "0"),
    ("silver", "critical", "pedidos sem cliente",
     "SELECT COUNT(*) FROM silver.orders o WHERE NOT EXISTS "
     "(SELECT 1 FROM silver.customers c WHERE c.customer_id = o.customer_id)", "0"),
    ("silver", "critical", "itens sem produto",
     "SELECT COUNT(*) FROM silver.order_items i WHERE NOT EXISTS "
     "(SELECT 1 FROM silver.products p WHERE p.product_id = i.product_id)", "0"),
    ("silver", "critical", "itens sem vendedor",
     "SELECT COUNT(*) FROM silver.order_items i WHERE NOT EXISTS "
     "(SELECT 1 FROM silver.sellers s WHERE s.seller_id = i.seller_id)", "0"),
    ("silver", "critical", "pagamentos sem pedido",
     "SELECT COUNT(*) FROM silver.order_payments p WHERE NOT EXISTS "
     "(SELECT 1 FROM silver.orders o WHERE o.order_id = p.order_id)", "0"),
    ("silver", "critical", "avaliações sem pedido",
     "SELECT COUNT(*) FROM silver.order_reviews r WHERE NOT EXISTS "
     "(SELECT 1 FROM silver.orders o WHERE o.order_id = r.order_id)", "0"),

    # ---------- SILVER: regras de negócio críticas ----------
    ("silver", "critical", "preço <= 0",
     "SELECT COUNT(*) FROM silver.order_items WHERE price <= 0", "0"),
    ("silver", "critical", "frete negativo",
     "SELECT COUNT(*) FROM silver.order_items WHERE freight_value < 0", "0"),
    ("silver", "critical", "pagamento negativo",
     "SELECT COUNT(*) FROM silver.order_payments WHERE payment_value < 0", "0"),
    ("silver", "critical", "nota de avaliação fora de 1 a 5",
     "SELECT COUNT(*) FROM silver.order_reviews WHERE review_score NOT BETWEEN 1 AND 5", "0"),
    ("silver", "critical", "peso ou dimensão negativos",
     "SELECT COUNT(*) FROM silver.products WHERE product_weight_g < 0 OR product_length_cm < 0 "
     "OR product_height_cm < 0 OR product_width_cm < 0", "0"),
    ("silver", "critical", "entrega anterior à compra",
     "SELECT COUNT(*) FROM silver.orders WHERE order_delivered_customer_date < order_purchase_timestamp", "0"),
    ("silver", "critical", "aprovação anterior à compra",
     "SELECT COUNT(*) FROM silver.orders WHERE order_approved_at < order_purchase_timestamp", "0"),

    # ---------- SILVER: ocorrências conhecidas (warning, baseline do relatório) ----------
    ("silver", "warning", "pedidos sem itens",
     "SELECT COUNT(*) FROM silver.orders o WHERE NOT EXISTS "
     "(SELECT 1 FROM silver.order_items i WHERE i.order_id = o.order_id)", "775"),
    ("silver", "warning", "pedidos shipped sem itens",
     "SELECT COUNT(*) FROM silver.orders o WHERE o.order_status = 'shipped' AND NOT EXISTS "
     "(SELECT 1 FROM silver.order_items i WHERE i.order_id = o.order_id)", "1"),
    ("silver", "warning", "pedidos sem pagamento",
     "SELECT COUNT(*) FROM silver.orders o WHERE NOT EXISTS "
     "(SELECT 1 FROM silver.order_payments p WHERE p.order_id = o.order_id)", "1"),
    ("silver", "warning", "pedidos sem avaliação",
     "SELECT COUNT(*) FROM silver.orders o WHERE NOT EXISTS "
     "(SELECT 1 FROM silver.order_reviews r WHERE r.order_id = o.order_id)", "768"),
    ("silver", "warning", "review_id repetidos",
     "SELECT COUNT(*) FROM (SELECT review_id FROM silver.order_reviews "
     "GROUP BY review_id HAVING COUNT(*) > 1) r", "789"),
    ("silver", "warning", "pagamentos com valor zero",
     "SELECT COUNT(*) FROM silver.order_payments WHERE payment_value = 0", "9"),
    ("silver", "warning", "pagamentos com 0 parcelas",
     "SELECT COUNT(*) FROM silver.order_payments WHERE payment_installments = 0", "2"),
    ("silver", "warning", "itens com frete zero",
     "SELECT COUNT(*) FROM silver.order_items WHERE freight_value = 0", "383"),
    ("silver", "warning", "produtos com peso zero",
     "SELECT COUNT(*) FROM silver.products WHERE product_weight_g = 0", "4"),
    ("silver", "warning", "produtos sem categoria",
     "SELECT COUNT(*) FROM silver.products WHERE product_category_name IS NULL", "610"),
    ("silver", "warning", "produtos com categoria sem tradução",
     "SELECT COUNT(*) FROM silver.products p WHERE p.product_category_name IS NOT NULL AND NOT EXISTS "
     "(SELECT 1 FROM silver.category_translation t WHERE t.product_category_name = p.product_category_name)", "13"),
    ("silver", "warning", "entrega anterior à aprovação",
     "SELECT COUNT(*) FROM silver.orders WHERE order_delivered_customer_date < order_approved_at", "61"),
    ("silver", "warning", "cancelados com data de entrega ao cliente",
     "SELECT COUNT(*) FROM silver.orders WHERE order_status = 'canceled' "
     "AND order_delivered_customer_date IS NOT NULL", "6"),
    ("silver", "warning", "cancelados com data de transportadora",
     "SELECT COUNT(*) FROM silver.orders WHERE order_status = 'canceled' "
     "AND order_delivered_carrier_date IS NOT NULL", "75"),
    ("silver", "warning", "delivered sem data real de entrega",
     "SELECT COUNT(*) FROM silver.orders WHERE order_status = 'delivered' "
     "AND order_delivered_customer_date IS NULL", "8"),
    ("silver", "warning", "geolocalização fora do Brasil",
     "SELECT COUNT(*) FROM silver.geolocation WHERE NOT is_within_brazil", "42"),

    # ---------- GOLD: integridade do modelo (analytics_validation) ----------
    ("gold", "critical", "fact_sales = silver.order_items (linhas)",
     "SELECT (SELECT COUNT(*) FROM gold.fact_sales) - (SELECT COUNT(*) FROM silver.order_items)", "0"),
    ("gold", "critical", "fact_payments = silver.order_payments (linhas)",
     "SELECT (SELECT COUNT(*) FROM gold.fact_payments) - (SELECT COUNT(*) FROM silver.order_payments)", "0"),
    ("gold", "critical", "receita gold = silver (sem duplicação por JOIN)",
     "SELECT (SELECT SUM(price) FROM gold.fact_sales) - (SELECT SUM(price) FROM silver.order_items)", "0.00"),
    ("gold", "critical", "pagamentos gold = silver",
     "SELECT (SELECT SUM(payment_value) FROM gold.fact_payments) "
     "- (SELECT SUM(payment_value) FROM silver.order_payments)", "0.00"),
    ("gold", "critical", "datas de compra fora da dim_date",
     "SELECT COUNT(*) FROM silver.orders o WHERE NOT EXISTS (SELECT 1 FROM gold.dim_date d "
     "WHERE d.date = o.order_purchase_timestamp::DATE)", "0"),

    # ---------- GOLD: indicadores auditados (comercial) ----------
    ("gold", "critical", "receita de produtos",
     "SELECT SUM(price) FROM gold.fact_sales", "13591643.70"),
    ("gold", "critical", "pedidos",
     "SELECT COUNT(DISTINCT order_id) FROM gold.fact_sales", "98666"),
    ("gold", "critical", "ticket médio",
     "SELECT ROUND(SUM(price) / COUNT(DISTINCT order_id), 2) FROM gold.fact_sales", "137.75"),
    ("gold", "critical", "clientes únicos",
     "SELECT COUNT(DISTINCT c.customer_unique_id) FROM gold.fact_sales f "
     "JOIN gold.dim_customer c ON c.customer_id = f.customer_id", "95420"),
    ("gold", "critical", "itens vendidos",
     "SELECT COUNT(*) FROM gold.fact_sales", "112650"),
    ("gold", "critical", "meses com vendas",
     "SELECT COUNT(DISTINCT d.year_month) FROM gold.fact_sales f "
     "JOIN gold.dim_date d ON d.date_key = f.purchase_date_key", "24"),
    ("gold", "critical", "valor credit_card",
     "SELECT SUM(payment_value) FROM gold.fact_payments WHERE payment_type = 'credit_card'", "12542084.19"),

    # ---------- GOLD: indicadores auditados (logística e investigação) ----------
    ("gold", "critical", "pedidos entregues com data válida",
     "SELECT COUNT(*) FROM gold.fact_order_delivery", "96470"),
    ("gold", "critical", "tempo médio de entrega (dias)",
     "SELECT ROUND(AVG(delivery_days)::NUMERIC, 2) FROM gold.fact_order_delivery", "12.56"),
    ("gold", "critical", "mediana de entrega (dias)",
     "SELECT ROUND((PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY delivery_days))::NUMERIC, 2) "
     "FROM gold.fact_order_delivery", "10.22"),
    ("gold", "critical", "entregas no prazo (pct)",
     "SELECT ROUND(100.0 * AVG(is_on_time::INT), 2) FROM gold.fact_order_delivery", "91.89"),
    ("gold", "critical", "antecipação média (dias)",
     "SELECT ROUND(AVG(-delay_days)::NUMERIC, 2) FROM gold.fact_order_delivery", "11.18"),
    ("gold", "critical", "pedidos com coordenadas",
     "SELECT COUNT(distance_km) FROM gold.fact_order_delivery", "95994"),
    ("gold", "critical", "Spearman distância x tempo",
     """SELECT ROUND(CORR(rd, rt)::NUMERIC, 3) FROM (
          SELECT RANK() OVER (ORDER BY distance_km)
                   + (COUNT(*) OVER (PARTITION BY distance_km) - 1) / 2.0 AS rd,
                 RANK() OVER (ORDER BY delivery_days)
                   + (COUNT(*) OVER (PARTITION BY delivery_days) - 1) / 2.0 AS rt
          FROM gold.fact_order_delivery WHERE distance_km IS NOT NULL) r""", "0.543"),
    ("gold", "critical", "Spearman distância x (real - estimada)",
     """SELECT ROUND(CORR(rd, ra)::NUMERIC, 3) FROM (
          SELECT RANK() OVER (ORDER BY distance_km)
                   + (COUNT(*) OVER (PARTITION BY distance_km) - 1) / 2.0 AS rd,
                 RANK() OVER (ORDER BY delay_days)
                   + (COUNT(*) OVER (PARTITION BY delay_days) - 1) / 2.0 AS ra
          FROM gold.fact_order_delivery WHERE distance_km IS NOT NULL) r""", "-0.179"),

    # ---------- GOLD: valores fixos das páginas Logística e Investigação ----------
    ("gold", "critical", "até 100 km: tempo médio (dias)",
     "SELECT ROUND(AVG(delivery_days)::NUMERIC, 2) FROM gold.fact_order_delivery "
     "WHERE distance_km <= 100", "6.51"),
    ("gold", "critical", "acima de 2.000 km: tempo médio (dias)",
     "SELECT ROUND(AVG(delivery_days)::NUMERIC, 2) FROM gold.fact_order_delivery "
     "WHERE distance_km > 2000", "21.18"),
    ("gold", "critical", "acima de 2.000 km: taxa de atraso (pct)",
     "SELECT ROUND(100.0 * AVG((NOT is_on_time)::INT), 2) FROM gold.fact_order_delivery "
     "WHERE distance_km > 2000", "13.66"),
    ("gold", "critical", "acima de 2.000 km: frete médio por pedido",
     "SELECT ROUND(AVG(freight_total), 2) FROM gold.fact_order_delivery "
     "WHERE distance_km > 2000", "39.88"),
    ("gold", "critical", "cortes das faixas de frete (quintis)",
     "SELECT ARRAY_TO_STRING(ARRAY(SELECT ROUND(q::NUMERIC, 2) FROM UNNEST("
     "PERCENTILE_CONT(ARRAY[0.2, 0.4, 0.6, 0.8]) WITHIN GROUP (ORDER BY freight_total)) q), ' | ') "
     "FROM gold.fact_order_delivery", "12.83 | 15.64 | 18.59 | 27.38"),
    ("gold", "critical", "status: total de pedidos",
     "SELECT SUM(orders) FROM gold.agg_order_status", "99441"),
    ("gold", "critical", "status: delivered",
     "SELECT orders FROM gold.agg_order_status WHERE order_status = 'delivered'", "96478"),
    ("gold", "critical", "AL: taxa de atraso (pct)",
     "SELECT ROUND(100.0 * AVG((NOT f.is_on_time)::INT), 2) FROM gold.fact_order_delivery f "
     "JOIN gold.dim_customer c ON c.customer_id = f.customer_id WHERE c.state = 'AL'", "23.93"),
]


# ============================================================
# RUN
# ============================================================

def run_quality_checks():

    print("=" * 60)
    print("BRAZILIAN E-COMMERCE | QUALITY CHECKS")
    print("=" * 60)

    with get_connection(autocommit=True) as conn, conn.cursor() as cur:

        cur.execute(
            "INSERT INTO control.pipeline_runs (pipeline_name, layer) "
            "VALUES (%s, 'quality') RETURNING run_id",
            (PIPELINE_NAME,),
        )
        run_id = cur.fetchone()[0]
        print(f"\nrun_id: {run_id}")

        critical_failures, warnings = [], []
        current_layer = None

        try:
            for layer, severity, name, sql, expected in CHECKS:

                if layer != current_layer:
                    current_layer = layer
                    print(f"\n[{layer.upper()}]")

                cur.execute(sql)
                value = cur.fetchone()[0]
                observed = "NULL" if value is None else str(value)
                passed = observed == expected

                cur.execute(
                    """
                    INSERT INTO control.quality_results
                        (run_id, layer, check_name, severity, expected, observed, passed)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (run_id, layer, name, severity, expected, observed, passed),
                )

                if passed:
                    label = "OK"
                elif severity == "critical":
                    label = "FAIL"
                    critical_failures.append(name)
                else:
                    label = "ALERTA"
                    warnings.append(name)

                detail = observed if passed else f"obtido={observed} esperado={expected}"
                print(f"  {label:<6} {name:<55} {detail}")

        except Exception as exc:
            cur.execute(
                "UPDATE control.pipeline_runs SET status = 'failed', finished_at = now(), "
                "error_message = %s WHERE run_id = %s",
                (f"{type(exc).__name__}: {exc}", run_id),
            )
            raise

        status = "failed" if critical_failures else "success"
        error = ("Críticas: " + "; ".join(critical_failures)) if critical_failures else None
        cur.execute(
            "UPDATE control.pipeline_runs SET status = %s, finished_at = now(), "
            "error_message = %s WHERE run_id = %s",
            (status, error, run_id),
        )

    total = len(CHECKS)
    print("\n" + "=" * 60)
    print(f"Verificações: {total} | críticas com falha: {len(critical_failures)} "
          f"| alertas: {len(warnings)}")

    if critical_failures:
        print("QUALITY CHECKS FAILED")
        print("=" * 60)
        raise SystemExit(1)

    print("QUALITY CHECKS PASSED")
    print("=" * 60)
    return run_id


if __name__ == "__main__":
    run_quality_checks()
