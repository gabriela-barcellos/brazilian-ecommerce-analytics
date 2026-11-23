-- Silver -> Gold | fact_sales (1 linha por item; mesma lógica do analytics_model.py)
INSERT INTO gold.fact_sales
    (order_id, order_item_id, customer_id, product_id, seller_id,
     purchase_date_key, order_purchase_timestamp, order_status,
     price, freight_value, item_total_value, _run_id)
SELECT
    i.order_id,
    i.order_item_id,
    o.customer_id,
    i.product_id,
    i.seller_id,
    TO_CHAR(o.order_purchase_timestamp, 'YYYYMMDD')::INTEGER,
    o.order_purchase_timestamp,
    o.order_status,
    i.price,
    i.freight_value,
    i.price + i.freight_value,
    %(run_id)s
FROM silver.order_items i
JOIN silver.orders o ON o.order_id = i.order_id;
