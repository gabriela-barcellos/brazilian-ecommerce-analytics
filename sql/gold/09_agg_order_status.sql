-- Silver -> Gold | agg_order_status (todos os pedidos, inclusive sem itens)
INSERT INTO gold.agg_order_status (order_status, orders, _run_id)
SELECT order_status, COUNT(*), %(run_id)s
FROM silver.orders
GROUP BY order_status;
