-- Bronze -> Silver | order_payments (granularidade: 1 linha por pagamento)
INSERT INTO silver.order_payments
    (order_id, payment_sequential, payment_type, payment_installments,
     payment_value, _run_id)
SELECT
    btrim(order_id),
    btrim(payment_sequential)::INTEGER,
    lower(btrim(payment_type)),
    btrim(payment_installments)::INTEGER,
    btrim(payment_value)::NUMERIC(12, 2),
    %(run_id)s
FROM bronze.order_payments;
