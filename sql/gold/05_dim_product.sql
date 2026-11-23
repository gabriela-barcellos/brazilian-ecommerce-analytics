-- Silver -> Gold | dim_product
-- Mesma regra de rótulo do dashboard.py:
--   NULL -> 'Sem categoria'; '_' -> ' '; iniciais maiúsculas.
INSERT INTO gold.dim_product
    (product_id, category_name, category_label, category_name_english,
     photos_qty, weight_g, length_cm, height_cm, width_cm, _run_id)
SELECT
    p.product_id,
    COALESCE(p.product_category_name, 'Sem categoria'),
    INITCAP(REPLACE(COALESCE(p.product_category_name, 'Sem categoria'), '_', ' ')),
    t.product_category_name_english,
    p.product_photos_qty,
    p.product_weight_g,
    p.product_length_cm,
    p.product_height_cm,
    p.product_width_cm,
    %(run_id)s
FROM silver.products p
LEFT JOIN silver.category_translation t
       ON t.product_category_name = p.product_category_name;
