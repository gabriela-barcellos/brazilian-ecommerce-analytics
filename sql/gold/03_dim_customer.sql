-- Silver -> Gold | dim_customer
INSERT INTO gold.dim_customer
    (customer_id, customer_unique_id, zip_code_prefix, city, state, lat, lng, _run_id)
SELECT
    c.customer_id,
    c.customer_unique_id,
    c.customer_zip_code_prefix,
    c.customer_city,
    c.customer_state,
    z.lat,
    z.lng,
    %(run_id)s
FROM silver.customers c
LEFT JOIN gold.zip_prefix_location z
       ON z.zip_code_prefix = c.customer_zip_code_prefix;
