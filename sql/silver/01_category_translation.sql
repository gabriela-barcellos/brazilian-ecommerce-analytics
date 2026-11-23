-- Bronze -> Silver | category_translation
INSERT INTO silver.category_translation
    (product_category_name, product_category_name_english, _run_id)
SELECT
    lower(btrim(product_category_name)),
    lower(btrim(product_category_name_english)),
    %(run_id)s
FROM bronze.category_translation;
