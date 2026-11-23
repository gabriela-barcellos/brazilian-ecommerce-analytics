-- Silver -> Gold | fact_payments (1 linha por pagamento)
INSERT INTO gold.fact_payments
    (order_id, payment_sequential, customer_id, purchase_date_key,
     payment_type, payment_installments, payment_value, _run_id)
SELECT
    p.order_id,
    p.payment_sequential,
    o.customer_id,
    TO_CHAR(o.order_purchase_timestamp, 'YYYYMMDD')::INTEGER,
    p.payment_type,
    p.payment_installments,
    p.payment_value,
    %(run_id)s
FROM silver.order_payments p
JOIN silver.orders o ON o.order_id = p.order_id;
