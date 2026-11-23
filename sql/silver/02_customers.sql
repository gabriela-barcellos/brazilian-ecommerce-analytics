-- Bronze -> Silver | customers
INSERT INTO silver.customers
    (customer_id, customer_unique_id, customer_zip_code_prefix,
     customer_city, customer_state, _run_id)
SELECT
    btrim(customer_id),
    btrim(customer_unique_id),
    btrim(customer_zip_code_prefix),
    lower(btrim(customer_city)),
    upper(btrim(customer_state)),
    %(run_id)s
FROM bronze.customers;
