-- Silver -> Gold | zip_prefix_location
-- MEDIANA de todos os pontos por prefixo (lat e lng separadamente).
-- Critério que reproduz exatamente os KPIs e as faixas da dashboard.
INSERT INTO gold.zip_prefix_location (zip_code_prefix, lat, lng, points, _run_id)
SELECT
    geolocation_zip_code_prefix,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY geolocation_lat),
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY geolocation_lng),
    COUNT(*),
    %(run_id)s
FROM silver.geolocation
GROUP BY geolocation_zip_code_prefix;
