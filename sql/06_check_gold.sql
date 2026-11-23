-- ============================================================
-- BRAZILIAN E-COMMERCE | 06 - VERIFICAÇÃO DA GOLD
-- Reconcilia a Gold com os indicadores auditados do projeto e com os
-- CSVs antigos de data/analytics (general_kpis, monthly_sales_metrics,
-- category_metrics, state_metrics, payment_metrics). "ok" deve ser t.
-- ============================================================

-- 1) Última execução Gold
SELECT run_id, status, finished_at - started_at AS duracao, error_message
FROM control.pipeline_runs
WHERE layer = 'gold'
ORDER BY run_id DESC
LIMIT 1;

-- 2) Cargas da última execução
SELECT dataset_name, rows_source AS origem, rows_loaded AS gold,
       rows_source = rows_loaded AS ok, status
FROM control.dataset_loads
WHERE run_id = (SELECT MAX(run_id) FROM control.pipeline_runs WHERE layer = 'gold')
ORDER BY load_id;

-- 3) Reconciliação
WITH
comercial AS (
    SELECT SUM(f.price)                     AS receita,
           COUNT(DISTINCT f.order_id)       AS pedidos,
           COUNT(DISTINCT c.customer_unique_id) AS clientes,
           COUNT(*)                         AS itens
    FROM gold.fact_sales f
    JOIN gold.dim_customer c ON c.customer_id = f.customer_id
),
logistica AS (
    SELECT COUNT(*)                                          AS pedidos,
           AVG(delivery_days)                                AS media,
           PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY delivery_days) AS mediana,
           100.0 * AVG(is_on_time::INT)                      AS pct_no_prazo,
           100.0 * AVG((NOT is_on_time)::INT)                AS pct_atraso,
           AVG(-delay_days)                                  AS antecipacao,
           COUNT(distance_km)                                AS com_coordenadas
    FROM gold.fact_order_delivery
),
ranks AS (
    -- Spearman = correlação de Pearson entre os postos (empates = posto médio)
    SELECT RANK() OVER (ORDER BY distance_km)   + (COUNT(*) OVER (PARTITION BY distance_km)   - 1) / 2.0 AS r_dist,
           RANK() OVER (ORDER BY delivery_days) + (COUNT(*) OVER (PARTITION BY delivery_days) - 1) / 2.0 AS r_dias,
           RANK() OVER (ORDER BY delay_days)    + (COUNT(*) OVER (PARTITION BY delay_days)    - 1) / 2.0 AS r_atraso
    FROM gold.fact_order_delivery
    WHERE distance_km IS NOT NULL
),
spearman AS (
    SELECT CORR(r_dist, r_dias) AS dist_dias, CORR(r_dist, r_atraso) AS dist_atraso FROM ranks
),
checks (grupo, verificacao, obtido, esperado) AS (
    SELECT 'comercial', 'receita de produtos',  (SELECT receita  FROM comercial)::TEXT, '13591643.70'
    UNION ALL SELECT 'comercial', 'pedidos',          (SELECT pedidos  FROM comercial)::TEXT, '98666'
    UNION ALL SELECT 'comercial', 'ticket médio',     (SELECT ROUND(receita / pedidos, 2) FROM comercial)::TEXT, '137.75'
    UNION ALL SELECT 'comercial', 'clientes únicos',  (SELECT clientes FROM comercial)::TEXT, '95420'
    UNION ALL SELECT 'comercial', 'itens vendidos',   (SELECT itens    FROM comercial)::TEXT, '112650'
    UNION ALL SELECT 'comercial', 'receita 2017-01',
        (SELECT SUM(f.price) FROM gold.fact_sales f
           JOIN gold.dim_date d ON d.date_key = f.purchase_date_key
          WHERE d.year_month = '2017-01')::TEXT, '120312.87'
    UNION ALL SELECT 'comercial', 'meses com vendas',
        (SELECT COUNT(DISTINCT d.year_month) FROM gold.fact_sales f
           JOIN gold.dim_date d ON d.date_key = f.purchase_date_key)::TEXT, '24'
    UNION ALL SELECT 'comercial', 'receita beleza_saude',
        (SELECT SUM(f.price) FROM gold.fact_sales f
           JOIN gold.dim_product p ON p.product_id = f.product_id
          WHERE p.category_name = 'beleza_saude')::TEXT, '1258681.34'
    UNION ALL SELECT 'comercial', 'receita SP',
        (SELECT SUM(f.price) FROM gold.fact_sales f
           JOIN gold.dim_customer c ON c.customer_id = f.customer_id
          WHERE c.state = 'SP')::TEXT, '5202955.05'
    UNION ALL SELECT 'comercial', 'pedidos SP',
        (SELECT COUNT(DISTINCT f.order_id) FROM gold.fact_sales f
           JOIN gold.dim_customer c ON c.customer_id = f.customer_id
          WHERE c.state = 'SP')::TEXT, '41375'
    UNION ALL SELECT 'pagamentos', 'valor credit_card',
        (SELECT SUM(payment_value) FROM gold.fact_payments WHERE payment_type = 'credit_card')::TEXT, '12542084.19'
    UNION ALL SELECT 'pagamentos', 'pedidos com credit_card',
        (SELECT COUNT(DISTINCT order_id) FROM gold.fact_payments WHERE payment_type = 'credit_card')::TEXT, '76505'
    UNION ALL SELECT 'logística', 'pedidos entregues com data válida', (SELECT pedidos FROM logistica)::TEXT, '96470'
    UNION ALL SELECT 'logística', 'tempo médio (dias)',      (SELECT ROUND(media::NUMERIC, 2)        FROM logistica)::TEXT, '12.56'
    UNION ALL SELECT 'logística', 'mediana (dias)',          (SELECT ROUND(mediana::NUMERIC, 2)      FROM logistica)::TEXT, '10.22'
    UNION ALL SELECT 'logística', 'entregas no prazo (%)',  (SELECT ROUND(pct_no_prazo::NUMERIC, 2) FROM logistica)::TEXT, '91.89'
    UNION ALL SELECT 'logística', 'entregas em atraso (%)', (SELECT ROUND(pct_atraso::NUMERIC, 2)   FROM logistica)::TEXT, '8.11'
    UNION ALL SELECT 'logística', 'antecipação média (dias)',(SELECT ROUND(antecipacao::NUMERIC, 2)  FROM logistica)::TEXT, '11.18'
    UNION ALL SELECT 'investigação', 'pedidos com coordenadas', (SELECT com_coordenadas FROM logistica)::TEXT, '95994'
    UNION ALL SELECT 'investigação', 'Spearman distância x tempo',
        (SELECT ROUND(dist_dias::NUMERIC, 3)   FROM spearman)::TEXT, '0.543'
    UNION ALL SELECT 'investigação', 'Spearman distância x (real - estimada)',
        (SELECT ROUND(dist_atraso::NUMERIC, 3) FROM spearman)::TEXT, '-0.179'
)
SELECT grupo, verificacao, obtido, esperado, obtido = esperado AS ok
FROM checks;
