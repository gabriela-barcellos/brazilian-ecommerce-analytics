-- Bronze -> Silver | orders
-- Datas vazias viram NULL (ex.: pedido ainda não entregue).
INSERT INTO silver.orders
    (order_id, customer_id, order_status, order_purchase_timestamp,
     order_approved_at, order_delivered_carrier_date,
     order_delivered_customer_date, order_estimated_delivery_date, _run_id)
SELECT
    btrim(order_id),
    btrim(customer_id),
    lower(btrim(order_status)),
    NULLIF(btrim(order_purchase_timestamp), '')::TIMESTAMP,
    NULLIF(btrim(order_approved_at), '')::TIMESTAMP,
    NULLIF(btrim(order_delivered_carrier_date), '')::TIMESTAMP,
    NULLIF(btrim(order_delivered_customer_date), '')::TIMESTAMP,
    NULLIF(btrim(order_estimated_delivery_date), '')::TIMESTAMP,
    %(run_id)s
FROM bronze.orders;
