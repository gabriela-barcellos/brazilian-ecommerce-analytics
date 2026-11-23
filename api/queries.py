"""
Consultas da API sobre a camada Gold.

Cada função recebe uma conexão psycopg aberta e devolve estruturas
simples (dict/list) prontas para JSON. Valores numéricos saem como float/int.

Regras de negócio preservadas
  * Receita de produtos = SUM(fact_sales.price) (sem frete).
  * Pedidos = COUNT(DISTINCT order_id); ticket = receita / pedidos.
  * Clientes únicos = COUNT(DISTINCT customer_unique_id).
  * Filtro de pagamento: pedidos com AO MENOS UM pagamento do tipo
    (semi-join em fact_payments); depois todos os itens desses pedidos.
    Nunca há JOIN entre itens e pagamentos para somar receita.
  * Set/2018 é parcial: fica fora da comparação com o mês anterior.
  * Logística: pedidos delivered com data real (gold.fact_order_delivery).
"""

from decimal import Decimal

PARTIAL_MONTH = "2018-09"

DISTANCE_BANDS = [  # (ordem, rótulo, limite superior inclusivo em km)
    (1, "Até 100 km", 100),
    (2, "100–300 km", 300),
    (3, "300–600 km", 600),
    (4, "600–1.000 km", 1000),
    (5, "1.000–2.000 km", 2000),
    (6, "Acima de 2.000 km", None),
]


# ============================================================
# HELPERS
# ============================================================

def _num(value):
    if isinstance(value, Decimal):
        return float(value)
    return value


def _rows(cur, sql, params=None):
    cur.execute(sql, params or {})
    cols = [c.name for c in cur.description]
    return [{k: _num(v) for k, v in zip(cols, row)} for row in cur.fetchall()]


def _one(cur, sql, params=None):
    rows = _rows(cur, sql, params)
    return rows[0] if rows else {}


# Itens de venda filtrados (página Comercial). Parâmetros:
# period ('AAAA-MM'), state ('SP'), category (category_name), payment (tipo).
FILTERED_SALES = """
    WITH filtered AS (
        SELECT f.order_id, f.price, d.year_month,
               c.customer_unique_id, c.state,
               p.category_name, p.category_label
        FROM gold.fact_sales f
        JOIN gold.dim_date d     ON d.date_key = f.purchase_date_key
        JOIN gold.dim_customer c ON c.customer_id = f.customer_id
        JOIN gold.dim_product p  ON p.product_id = f.product_id
        WHERE (%(period)s::TEXT   IS NULL OR d.year_month = %(period)s)
          AND (%(state)s::TEXT    IS NULL OR c.state = %(state)s)
          AND (%(category)s::TEXT IS NULL OR p.category_name = %(category)s)
          -- pedido com ao menos um pagamento do tipo (IN = semi-join; mais
          -- rápido que EXISTS correlacionado aqui, mesmo resultado)
          AND (%(payment)s::TEXT  IS NULL OR f.order_id IN (
                SELECT fp.order_id FROM gold.fact_payments fp
                WHERE fp.payment_type = %(payment)s))
    )
"""


# ============================================================
# FILTROS
# ============================================================

def filter_options(conn):
    with conn.cursor() as cur:
        periods = _rows(cur, """
            SELECT DISTINCT d.year_month AS value
            FROM gold.fact_sales f JOIN gold.dim_date d ON d.date_key = f.purchase_date_key
            ORDER BY 1""")
        states = _rows(cur, """
            SELECT DISTINCT c.state AS value
            FROM gold.fact_sales f JOIN gold.dim_customer c ON c.customer_id = f.customer_id
            ORDER BY 1""")
        categories = _rows(cur, """
            SELECT DISTINCT p.category_name AS value, p.category_label AS label
            FROM gold.fact_sales f JOIN gold.dim_product p ON p.product_id = f.product_id
            ORDER BY 1""")
        # Só tipos usados por pedidos com itens (igual à dashboard original:
        # 'not_defined' só aparece em pedidos sem itens e ficaria sempre vazio).
        payments = _rows(cur, """
            SELECT DISTINCT fp.payment_type AS value
            FROM gold.fact_payments fp
            WHERE fp.order_id IN (SELECT order_id FROM gold.fact_sales)
            ORDER BY 1""")

    return {
        "periods": [r["value"] for r in periods],
        "partial_period": PARTIAL_MONTH,
        "states": [r["value"] for r in states],
        "categories": categories,
        "payment_types": [r["value"] for r in payments],
    }


# ============================================================
# PÁGINA 1 — COMERCIAL
# ============================================================

def commercial(conn, period=None, state=None, category=None, payment=None, top=10):
    params = {"period": period, "state": state, "category": category, "payment": payment}

    with conn.cursor() as cur:
        kpis = _one(cur, FILTERED_SALES + """
            SELECT COALESCE(SUM(price), 0)            AS revenue,
                   COUNT(DISTINCT order_id)           AS orders,
                   COUNT(DISTINCT customer_unique_id) AS customers
            FROM filtered""", params)
        kpis["average_ticket"] = kpis["revenue"] / kpis["orders"] if kpis["orders"] else 0.0

        monthly = _rows(cur, FILTERED_SALES + """
            SELECT year_month, SUM(price) AS revenue
            FROM filtered GROUP BY year_month ORDER BY year_month""", params)

        categories = _rows(cur, FILTERED_SALES + """
            SELECT category_name, category_label, SUM(price) AS revenue
            FROM filtered GROUP BY category_name, category_label
            ORDER BY revenue DESC LIMIT %(top)s""", {**params, "top": top})

        states = _rows(cur, FILTERED_SALES + """
            SELECT state, SUM(price) AS revenue
            FROM filtered GROUP BY state
            ORDER BY revenue DESC LIMIT %(top)s""", {**params, "top": top})

        # Pagamentos dos pedidos filtrados (granularidade de pagamento,
        # sem multiplicar por itens). Com filtro de tipo, só aquele tipo.
        payments = _rows(cur, FILTERED_SALES + """
            SELECT fp.payment_type, SUM(fp.payment_value) AS value
            FROM gold.fact_payments fp
            WHERE fp.order_id IN (SELECT order_id FROM filtered)
              AND (%(payment)s::TEXT IS NULL OR fp.payment_type = %(payment)s)
            GROUP BY fp.payment_type
            ORDER BY value DESC""", params)

        comparison = None
        if period and period != PARTIAL_MONTH:
            prev = _one(cur, """
                SELECT MAX(d.year_month) AS previous
                FROM gold.fact_sales f JOIN gold.dim_date d ON d.date_key = f.purchase_date_key
                WHERE d.year_month < %(period)s AND d.year_month <> %(partial)s""",
                {"period": period, "partial": PARTIAL_MONTH}).get("previous")
            if prev:
                prev_rev = _one(cur, FILTERED_SALES + """
                    SELECT COALESCE(SUM(price), 0) AS revenue FROM filtered""",
                    {**params, "period": prev})["revenue"]
                comparison = {
                    "previous_period": prev,
                    "previous_revenue": prev_rev,
                    "change_pct": (kpis["revenue"] - prev_rev) / prev_rev * 100 if prev_rev else None,
                }

    return {
        "filters": params,
        "kpis": kpis,
        "comparison": comparison,
        "monthly": monthly,
        "categories": categories,
        "states": states,
        "payments": payments,
    }


# ============================================================
# PÁGINA 2 — LOGÍSTICA
# ============================================================

def logistics(conn, states_limit=12):
    with conn.cursor() as cur:
        kpis = _one(cur, """
            SELECT COUNT(*)                                                    AS orders,
                   AVG(delivery_days)                                          AS avg_days,
                   PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY delivery_days)  AS median_days,
                   100.0 * AVG(is_on_time::INT)                                AS on_time_pct,
                   100.0 * AVG((NOT is_on_time)::INT)                          AS late_pct,
                   AVG(-delay_days)                                            AS early_days
            FROM gold.fact_order_delivery""")

        monthly = _rows(cur, """
            SELECT d.year_month,
                   COUNT(*)                     AS orders,
                   AVG(f.delivery_days)         AS avg_days,
                   AVG(f.is_on_time::INT)::FLOAT AS on_time
            FROM gold.fact_order_delivery f
            JOIN gold.dim_date d ON d.date_key = f.purchase_date_key
            GROUP BY d.year_month ORDER BY d.year_month""")

        states = _rows(cur, """
            SELECT c.state                            AS customer_state,
                   COUNT(*)                           AS orders,
                   AVG(f.delivery_days)               AS avg_days,
                   AVG(f.is_on_time::INT)::FLOAT      AS on_time,
                   AVG((NOT f.is_on_time)::INT)::FLOAT AS late
            FROM gold.fact_order_delivery f
            JOIN gold.dim_customer c ON c.customer_id = f.customer_id
            GROUP BY c.state
            ORDER BY on_time ASC, c.state
            LIMIT %(limit)s""", {"limit": states_limit})

        status = _rows(cur, """
            SELECT order_status, orders FROM gold.agg_order_status ORDER BY orders DESC""")

    total = sum(s["orders"] for s in status)
    for s in status:
        s["share_pct"] = s["orders"] / total * 100 if total else 0.0

    return {"kpis": kpis, "monthly": monthly, "states": states,
            "status": status, "total_orders": total}


# ============================================================
# PÁGINA 3 — INVESTIGAÇÃO
# ============================================================

def investigation(conn, states_limit=8):
    band_case = "CASE " + " ".join(
        f"WHEN distance_km <= {limit} THEN {order}"
        for order, _, limit in DISTANCE_BANDS if limit is not None
    ) + f" ELSE {DISTANCE_BANDS[-1][0]} END"

    with conn.cursor() as cur:
        spearman = _one(cur, """
            SELECT COUNT(*)                AS orders_with_distance,
                   CORR(r_dist, r_days)    AS spearman_distance_days,
                   CORR(r_dist, r_delay)   AS spearman_distance_delay
            FROM (
                SELECT RANK() OVER (ORDER BY distance_km)
                         + (COUNT(*) OVER (PARTITION BY distance_km) - 1) / 2.0   AS r_dist,
                       RANK() OVER (ORDER BY delivery_days)
                         + (COUNT(*) OVER (PARTITION BY delivery_days) - 1) / 2.0 AS r_days,
                       RANK() OVER (ORDER BY delay_days)
                         + (COUNT(*) OVER (PARTITION BY delay_days) - 1) / 2.0    AS r_delay
                FROM gold.fact_order_delivery
                WHERE distance_km IS NOT NULL
            ) r""")

        bands = _rows(cur, f"""
            SELECT {band_case}                            AS band,
                   COUNT(*)                               AS orders,
                   AVG(delivery_days)                     AS avg_days,
                   100.0 * AVG((NOT is_on_time)::INT)     AS late_pct,
                   AVG(freight_total)                     AS avg_freight
            FROM gold.fact_order_delivery
            WHERE distance_km IS NOT NULL
            GROUP BY 1 ORDER BY 1""")
        labels = {order: label for order, label, _ in DISTANCE_BANDS}
        for b in bands:
            b["label"] = labels[b["band"]]

        cuts = _one(cur, """
            SELECT PERCENTILE_CONT(ARRAY[0.2, 0.4, 0.6, 0.8])
                   WITHIN GROUP (ORDER BY freight_total) AS cuts
            FROM gold.fact_order_delivery""")["cuts"]
        cuts = [float(c) for c in cuts]

        freight_bands = _rows(cur, """
            SELECT CASE WHEN freight_total <= %(c1)s THEN 1
                        WHEN freight_total <= %(c2)s THEN 2
                        WHEN freight_total <= %(c3)s THEN 3
                        WHEN freight_total <= %(c4)s THEN 4
                        ELSE 5 END                        AS band,
                   COUNT(*)                               AS orders,
                   AVG(freight_total)                     AS avg_freight,
                   100.0 * AVG((NOT is_on_time)::INT)     AS late_pct
            FROM gold.fact_order_delivery
            GROUP BY 1 ORDER BY 1""",
            {"c1": cuts[0], "c2": cuts[1], "c3": cuts[2], "c4": cuts[3]})
        bounds = [None] + cuts + [None]
        for b in freight_bands:
            b["lower"], b["upper"] = bounds[b["band"] - 1], bounds[b["band"]]

        states = _rows(cur, """
            SELECT c.state                                 AS customer_state,
                   COUNT(*)                                AS orders,
                   100.0 * AVG((NOT f.is_on_time)::INT)    AS late_pct
            FROM gold.fact_order_delivery f
            JOIN gold.dim_customer c ON c.customer_id = f.customer_id
            GROUP BY c.state
            ORDER BY late_pct DESC, c.state
            LIMIT %(limit)s""", {"limit": states_limit})

    over_2000 = next((b for b in bands if b["band"] == DISTANCE_BANDS[-1][0]), {})
    kpis = {
        **spearman,
        "late_pct_over_2000km": over_2000.get("late_pct"),
        "avg_freight_over_2000km": over_2000.get("avg_freight"),
    }
    return {"kpis": kpis, "distance_bands": bands, "freight_cuts": cuts,
            "freight_bands": freight_bands, "states": states}


# ============================================================
# SAÚDE / MONITORAMENTO
# ============================================================

def health(conn):
    with conn.cursor() as cur:
        runs = _rows(cur, """
            SELECT DISTINCT ON (layer) layer, run_id, status, started_at::TEXT, finished_at::TEXT
            FROM control.pipeline_runs
            ORDER BY layer, run_id DESC""")
        quality = _one(cur, """
            SELECT q.run_id,
                   COUNT(*)                                                   AS checks,
                   COUNT(*) FILTER (WHERE NOT passed AND severity = 'critical') AS critical_failures,
                   COUNT(*) FILTER (WHERE NOT passed AND severity = 'warning')  AS warnings
            FROM control.quality_results q
            WHERE q.run_id = (SELECT MAX(run_id) FROM control.quality_results)
            GROUP BY q.run_id""")
    return {"database": "ok", "last_runs": runs, "last_quality": quality or None}
