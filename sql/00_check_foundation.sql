-- ============================================================
-- BRAZILIAN E-COMMERCE | 00 - VERIFICAÇÃO DA ETAPA 1
-- Esperado: 4 schemas, 2 tabelas em control, 9 em bronze.
-- ============================================================

-- 1) Schemas
SELECT schema_name
FROM information_schema.schemata
WHERE schema_name IN ('bronze', 'silver', 'gold', 'control')
ORDER BY schema_name;

-- 2) Quantidade de tabelas por schema
SELECT table_schema, COUNT(*) AS tabelas
FROM information_schema.tables
WHERE table_schema IN ('bronze', 'silver', 'gold', 'control')
GROUP BY table_schema
ORDER BY table_schema;

-- 3) Tabelas e número de colunas
SELECT table_schema, table_name, COUNT(*) AS colunas
FROM information_schema.columns
WHERE table_schema IN ('bronze', 'control')
GROUP BY table_schema, table_name
ORDER BY table_schema, table_name;
