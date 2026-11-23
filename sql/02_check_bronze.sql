-- ============================================================
-- BRAZILIAN E-COMMERCE | 02 - VERIFICAÇÃO DA INGESTÃO BRONZE
-- ============================================================

-- 1) Última execução
SELECT run_id, status, started_at, finished_at,
       finished_at - started_at AS duracao, error_message
FROM control.pipeline_runs
WHERE layer = 'bronze'
ORDER BY run_id DESC
LIMIT 1;

-- 2) Cargas da última execução: CSV x banco
SELECT dataset_name, rows_source, rows_loaded,
       rows_source = rows_loaded AS bate, status
FROM control.dataset_loads
WHERE run_id = (SELECT MAX(run_id) FROM control.pipeline_runs WHERE layer = 'bronze')
ORDER BY dataset_name;

-- 3) Contagem atual nas tabelas Bronze (não pode duplicar ao reexecutar)
SELECT 'customers' AS tabela, COUNT(*) FROM bronze.customers
UNION ALL SELECT 'geolocation', COUNT(*) FROM bronze.geolocation
UNION ALL SELECT 'order_items', COUNT(*) FROM bronze.order_items
UNION ALL SELECT 'order_payments', COUNT(*) FROM bronze.order_payments
UNION ALL SELECT 'order_reviews', COUNT(*) FROM bronze.order_reviews
UNION ALL SELECT 'orders', COUNT(*) FROM bronze.orders
UNION ALL SELECT 'products', COUNT(*) FROM bronze.products
UNION ALL SELECT 'sellers', COUNT(*) FROM bronze.sellers
UNION ALL SELECT 'category_translation', COUNT(*) FROM bronze.category_translation
ORDER BY 1;
