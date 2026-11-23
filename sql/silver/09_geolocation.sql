-- Bronze -> Silver | geolocation
-- Mantém todas as linhas (inclusive duplicadas). Retângulo aproximado do
-- Brasil: latitude -34 a 5.5, longitude -74 a -34.5.
INSERT INTO silver.geolocation
    (geolocation_zip_code_prefix, geolocation_lat, geolocation_lng,
     geolocation_city, geolocation_state, is_within_brazil, _run_id)
SELECT
    zip, lat, lng, city, state,
    (lat BETWEEN -34 AND 5.5 AND lng BETWEEN -74 AND -34.5),
    %(run_id)s
FROM (
    SELECT
        btrim(geolocation_zip_code_prefix)          AS zip,
        btrim(geolocation_lat)::DOUBLE PRECISION    AS lat,
        btrim(geolocation_lng)::DOUBLE PRECISION    AS lng,
        lower(btrim(geolocation_city))              AS city,
        upper(btrim(geolocation_state))             AS state
    FROM bronze.geolocation
) g;
