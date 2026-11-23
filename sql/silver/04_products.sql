-- Bronze -> Silver | products
-- Corrige os nomes "lenght" -> "length". Nulos preservados.
INSERT INTO silver.products
    (product_id, product_category_name, product_name_length,
     product_description_length, product_photos_qty, product_weight_g,
     product_length_cm, product_height_cm, product_width_cm, _run_id)
SELECT
    btrim(product_id),
    lower(NULLIF(btrim(product_category_name), '')),
    NULLIF(btrim(product_name_lenght), '')::INTEGER,
    NULLIF(btrim(product_description_lenght), '')::INTEGER,
    NULLIF(btrim(product_photos_qty), '')::INTEGER,
    NULLIF(btrim(product_weight_g), '')::INTEGER,
    NULLIF(btrim(product_length_cm), '')::INTEGER,
    NULLIF(btrim(product_height_cm), '')::INTEGER,
    NULLIF(btrim(product_width_cm), '')::INTEGER,
    %(run_id)s
FROM bronze.products;
