-- Silver/Gold -> Gold | fact_order_delivery
-- Pedidos delivered com data real de entrega.
-- distance_km: MÉDIA, entre os itens do pedido, da distância Haversine
--   (raio 6.371 km) cliente -> vendedor do item. Itens cujo vendedor não
--   tem coordenada são ignorados na média; NULL se nenhum tiver.
--   (Nota metodológica da dashboard: "pedidos com múltiplos vendedores
--   usam distância média".)
-- seller_id: vendedor do item 1, apenas como referência.
INSERT INTO gold.fact_order_delivery
    (order_id, customer_id, seller_id, purchase_date_key,
     order_purchase_timestamp, order_delivered_customer_date,
     order_estimated_delivery_date, delivery_days, estimated_days,
     delay_days, is_on_time, items_qty, freight_total, distance_km, _run_id)
WITH item_distance AS (
    SELECT
        i.order_id,
        i.order_item_id,
        i.seller_id,
        i.freight_value,
        2 * 6371 * ASIN(SQRT(
              POWER(SIN(RADIANS(s.lat - c.lat) / 2), 2)
            + COS(RADIANS(c.lat)) * COS(RADIANS(s.lat))
            * POWER(SIN(RADIANS(s.lng - c.lng) / 2), 2)
        )) AS distance_km
    FROM silver.order_items i
    JOIN silver.orders o       ON o.order_id = i.order_id
    JOIN gold.dim_customer c   ON c.customer_id = o.customer_id
    JOIN gold.dim_seller s     ON s.seller_id = i.seller_id
),
items AS (
    SELECT
        order_id,
        COUNT(*)                                          AS items_qty,
        SUM(freight_value)                                AS freight_total,
        AVG(distance_km)                                  AS distance_km,
        MIN(seller_id) FILTER (WHERE order_item_id = 1)   AS first_seller_id
    FROM item_distance
    GROUP BY order_id
)
SELECT
    o.order_id,
    o.customer_id,
    i.first_seller_id,
    TO_CHAR(o.order_purchase_timestamp, 'YYYYMMDD')::INTEGER,
    o.order_purchase_timestamp,
    o.order_delivered_customer_date,
    o.order_estimated_delivery_date,
    EXTRACT(EPOCH FROM o.order_delivered_customer_date - o.order_purchase_timestamp) / 86400.0,
    EXTRACT(EPOCH FROM o.order_estimated_delivery_date - o.order_purchase_timestamp) / 86400.0,
    EXTRACT(EPOCH FROM o.order_delivered_customer_date - o.order_estimated_delivery_date) / 86400.0,
    o.order_delivered_customer_date <= o.order_estimated_delivery_date,
    COALESCE(i.items_qty, 0),
    COALESCE(i.freight_total, 0),
    i.distance_km,
    %(run_id)s
FROM silver.orders o
LEFT JOIN items i ON i.order_id = o.order_id
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL;
