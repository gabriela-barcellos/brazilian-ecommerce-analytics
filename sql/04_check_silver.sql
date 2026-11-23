-- ============================================================
-- BRAZILIAN E-COMMERCE | 04 - VERIFICAÇÃO DA SILVER
-- Compara a Silver com os números do reports/data_quality_report.md
-- e com os indicadores auditados do projeto. Coluna "ok" deve ser t.
-- ============================================================

-- 1) Última execução Silver
SELECT run_id, status, finished_at - started_at AS duracao, error_message
FROM control.pipeline_runs
WHERE layer = 'silver'
ORDER BY run_id DESC
LIMIT 1;

-- 2) Cargas da última execução: Bronze x Silver
SELECT dataset_name, rows_source AS bronze, rows_loaded AS silver,
       rows_source = rows_loaded AS ok, status
FROM control.dataset_loads
WHERE run_id = (SELECT MAX(run_id) FROM control.pipeline_runs WHERE layer = 'silver')
ORDER BY load_id;

-- 3) Reconciliação com resultados já auditados
WITH checks (verificacao, obtido, esperado) AS (
    SELECT 'receita de produtos (soma price)',
           (SELECT SUM(price) FROM silver.order_items)::TEXT, '13591643.70'
    UNION ALL
    SELECT 'pedidos com itens',
           (SELECT COUNT(DISTINCT order_id) FROM silver.order_items)::TEXT, '98666'
    UNION ALL
    SELECT 'clientes únicos (customer_unique_id em pedidos com itens)',
           (SELECT COUNT(DISTINCT c.customer_unique_id)
              FROM silver.order_items i
              JOIN silver.orders o    ON o.order_id = i.order_id
              JOIN silver.customers c ON c.customer_id = o.customer_id)::TEXT, '95420'
    UNION ALL
    SELECT 'pedidos delivered',
           (SELECT COUNT(*) FROM silver.orders WHERE order_status = 'delivered')::TEXT, '96478'
    UNION ALL
    SELECT 'delivered sem data real de entrega',
           (SELECT COUNT(*) FROM silver.orders
             WHERE order_status = 'delivered'
               AND order_delivered_customer_date IS NULL)::TEXT, '8'
    UNION ALL
    SELECT 'nulos order_approved_at',
           (SELECT COUNT(*) FROM silver.orders WHERE order_approved_at IS NULL)::TEXT, '160'
    UNION ALL
    SELECT 'nulos order_delivered_customer_date',
           (SELECT COUNT(*) FROM silver.orders WHERE order_delivered_customer_date IS NULL)::TEXT, '2965'
    UNION ALL
    SELECT 'produtos sem categoria',
           (SELECT COUNT(*) FROM silver.products WHERE product_category_name IS NULL)::TEXT, '610'
    UNION ALL
    SELECT 'produtos com categoria sem tradução',
           (SELECT COUNT(*) FROM silver.products p
             WHERE p.product_category_name IS NOT NULL
               AND NOT EXISTS (SELECT 1 FROM silver.category_translation t
                                WHERE t.product_category_name = p.product_category_name))::TEXT, '13'
    UNION ALL
    SELECT 'review_id repetidos',
           (SELECT COUNT(*) FROM (SELECT review_id FROM silver.order_reviews
                                   GROUP BY review_id HAVING COUNT(*) > 1) r)::TEXT, '789'
    UNION ALL
    SELECT 'pagamentos com valor zero',
           (SELECT COUNT(*) FROM silver.order_payments WHERE payment_value = 0)::TEXT, '9'
    UNION ALL
    SELECT 'pagamentos com 0 parcelas',
           (SELECT COUNT(*) FROM silver.order_payments WHERE payment_installments = 0)::TEXT, '2'
    UNION ALL
    SELECT 'itens com frete zero',
           (SELECT COUNT(*) FROM silver.order_items WHERE freight_value = 0)::TEXT, '383'
    UNION ALL
    SELECT 'entrega antes da aprovação',
           (SELECT COUNT(*) FROM silver.orders
             WHERE order_delivered_customer_date < order_approved_at)::TEXT, '61'
    UNION ALL
    SELECT 'geolocalização fora do Brasil',
           (SELECT COUNT(*) FROM silver.geolocation WHERE NOT is_within_brazil)::TEXT, '42'
    UNION ALL
    SELECT 'geolocalização: linhas duplicadas',
           (SELECT COUNT(*) - COUNT(DISTINCT (geolocation_zip_code_prefix, geolocation_lat,
                                              geolocation_lng, geolocation_city, geolocation_state))
              FROM silver.geolocation)::TEXT, '261831'
)
SELECT verificacao, obtido, esperado, obtido = esperado AS ok
FROM checks;
