-- Silver -> Gold | dim_date
-- Calendário contínuo do primeiro ao último dia de compra.
INSERT INTO gold.dim_date
    (date_key, date, year, quarter, month, year_month, day, day_of_week, is_weekend, _run_id)
SELECT
    TO_CHAR(d, 'YYYYMMDD')::INTEGER,
    d,
    EXTRACT(YEAR FROM d),
    EXTRACT(QUARTER FROM d),
    EXTRACT(MONTH FROM d),
    TO_CHAR(d, 'YYYY-MM'),
    EXTRACT(DAY FROM d),
    EXTRACT(ISODOW FROM d) - 1,
    EXTRACT(ISODOW FROM d) IN (6, 7),
    %(run_id)s
FROM (
    -- DATE + inteiro: sem fuso horário. (generate_series com INTERVAL usa
    -- timestamptz e pode pular dias de início do horário de verão.)
    SELECT b.first_day + n AS d
    FROM (SELECT MIN(order_purchase_timestamp)::DATE AS first_day,
                 MAX(order_purchase_timestamp)::DATE AS last_day
          FROM silver.orders) b
    CROSS JOIN generate_series(0, b.last_day - b.first_day) AS n
) dates;
