-- Bronze -> Silver | order_items (granularidade: 1 linha por item do pedido)
INSERT INTO silver.order_items
    (order_id, order_item_id, product_id, seller_id, shipping_limit_date,
     price, freight_value, _run_id)
SELECT
    btrim(order_id),
    btrim(order_item_id)::INTEGER,
    btrim(product_id),
    btrim(seller_id),
    btrim(shipping_limit_date)::TIMESTAMP,
    btrim(price)::NUMERIC(12, 2),
    btrim(freight_value)::NUMERIC(12, 2),
    %(run_id)s
FROM bronze.order_items;
