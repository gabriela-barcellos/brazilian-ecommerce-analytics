-- Silver -> Gold | dim_seller
INSERT INTO gold.dim_seller
    (seller_id, zip_code_prefix, city, state, lat, lng, _run_id)
SELECT
    s.seller_id,
    s.seller_zip_code_prefix,
    s.seller_city,
    s.seller_state,
    z.lat,
    z.lng,
    %(run_id)s
FROM silver.sellers s
LEFT JOIN gold.zip_prefix_location z
       ON z.zip_code_prefix = s.seller_zip_code_prefix;
