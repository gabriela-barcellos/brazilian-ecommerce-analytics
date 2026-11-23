-- Bronze -> Silver | sellers
INSERT INTO silver.sellers
    (seller_id, seller_zip_code_prefix, seller_city, seller_state, _run_id)
SELECT
    btrim(seller_id),
    btrim(seller_zip_code_prefix),
    lower(btrim(seller_city)),
    upper(btrim(seller_state)),
    %(run_id)s
FROM bronze.sellers;
