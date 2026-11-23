-- ============================================================
-- BRAZILIAN E-COMMERCE | 05 - TABELAS GOLD (STAR SCHEMA)
-- Idempotente: pode ser executado mais de uma vez.
--
-- Fatos
--   gold.fact_sales           1 linha por ITEM do pedido (todos os status)
--   gold.fact_payments        1 linha por PAGAMENTO do pedido
--   gold.fact_order_delivery  1 linha por pedido delivered com data real
-- Dimensões
--   gold.dim_date, gold.dim_customer, gold.dim_product, gold.dim_seller
-- Apoio
--   gold.zip_prefix_location  coordenada representativa por prefixo de CEP
--
-- Chaves: usamos as chaves naturais da Olist (hashes estáveis e únicos),
-- sem chaves substitutas, para manter o modelo simples e rastreável.
--
-- REGRA: fact_sales e fact_payments têm granularidades diferentes.
-- Nunca juntar as duas para somar receita. Para filtrar vendas por forma
-- de pagamento, use EXISTS em fact_payments (pedido com ao menos um
-- pagamento do tipo) e some fact_sales.price.
-- ============================================================

-- Coordenada representativa = MEDIANA de todos os pontos do prefixo em
-- silver.geolocation (sem remover duplicatas nem pontos fora do Brasil).
-- É o critério que reproduz os indicadores auditados (95.994 pedidos com
-- coordenadas; Spearman 0,543 e -0,179) e as faixas da página Investigação.
CREATE TABLE IF NOT EXISTS gold.zip_prefix_location (
    zip_code_prefix  TEXT PRIMARY KEY,
    lat              DOUBLE PRECISION NOT NULL,
    lng              DOUBLE PRECISION NOT NULL,
    points           INTEGER NOT NULL,
    _run_id     BIGINT      NOT NULL REFERENCES control.pipeline_runs (run_id),
    _loaded_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS gold.dim_date (
    date_key     INTEGER PRIMARY KEY,          -- AAAAMMDD
    date         DATE    NOT NULL UNIQUE,
    year         SMALLINT NOT NULL,
    quarter      SMALLINT NOT NULL,
    month        SMALLINT NOT NULL,
    year_month   CHAR(7)  NOT NULL,            -- 'AAAA-MM'
    day          SMALLINT NOT NULL,
    day_of_week  SMALLINT NOT NULL,            -- 0 = segunda ... 6 = domingo
    is_weekend   BOOLEAN  NOT NULL,
    _run_id     BIGINT      NOT NULL REFERENCES control.pipeline_runs (run_id),
    _loaded_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS gold.dim_customer (
    customer_id         TEXT PRIMARY KEY,
    customer_unique_id  TEXT NOT NULL,
    zip_code_prefix     TEXT NOT NULL,
    city                TEXT NOT NULL,
    state               CHAR(2) NOT NULL,
    lat                 DOUBLE PRECISION,      -- NULL se o CEP não tem coordenada
    lng                 DOUBLE PRECISION,
    _run_id     BIGINT      NOT NULL REFERENCES control.pipeline_runs (run_id),
    _loaded_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS gold.dim_seller (
    seller_id        TEXT PRIMARY KEY,
    zip_code_prefix  TEXT NOT NULL,
    city             TEXT NOT NULL,
    state            CHAR(2) NOT NULL,
    lat              DOUBLE PRECISION,
    lng              DOUBLE PRECISION,
    _run_id     BIGINT      NOT NULL REFERENCES control.pipeline_runs (run_id),
    _loaded_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- category_name: NULL da origem vira 'Sem categoria' (mesma regra do
-- dashboard.py). category_label: '_' -> ' ' e iniciais maiúsculas.
-- category_name_english: NULL quando não há tradução (13 produtos).
CREATE TABLE IF NOT EXISTS gold.dim_product (
    product_id             TEXT PRIMARY KEY,
    category_name          TEXT NOT NULL,
    category_label         TEXT NOT NULL,
    category_name_english  TEXT,
    photos_qty             INTEGER,
    weight_g               INTEGER,
    length_cm              INTEGER,
    height_cm              INTEGER,
    width_cm               INTEGER,
    _run_id     BIGINT      NOT NULL REFERENCES control.pipeline_runs (run_id),
    _loaded_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- price = receita de produtos (sem frete).
CREATE TABLE IF NOT EXISTS gold.fact_sales (
    order_id                  TEXT    NOT NULL,
    order_item_id             INTEGER NOT NULL,
    customer_id               TEXT    NOT NULL REFERENCES gold.dim_customer (customer_id),
    product_id                TEXT    NOT NULL REFERENCES gold.dim_product (product_id),
    seller_id                 TEXT    NOT NULL REFERENCES gold.dim_seller (seller_id),
    purchase_date_key         INTEGER NOT NULL REFERENCES gold.dim_date (date_key),
    order_purchase_timestamp  TIMESTAMP NOT NULL,
    order_status              TEXT    NOT NULL,
    price                     NUMERIC(12, 2) NOT NULL,
    freight_value             NUMERIC(12, 2) NOT NULL,
    item_total_value          NUMERIC(12, 2) NOT NULL,
    _run_id     BIGINT      NOT NULL REFERENCES control.pipeline_runs (run_id),
    _loaded_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (order_id, order_item_id)
);

CREATE TABLE IF NOT EXISTS gold.fact_payments (
    order_id                TEXT    NOT NULL,
    payment_sequential      INTEGER NOT NULL,
    customer_id             TEXT    NOT NULL REFERENCES gold.dim_customer (customer_id),
    purchase_date_key       INTEGER NOT NULL REFERENCES gold.dim_date (date_key),
    payment_type            TEXT    NOT NULL,
    payment_installments    INTEGER NOT NULL,
    payment_value           NUMERIC(12, 2) NOT NULL,
    _run_id     BIGINT      NOT NULL REFERENCES control.pipeline_runs (run_id),
    _loaded_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (order_id, payment_sequential)
);

-- Pedidos delivered com data real de entrega (96.470).
-- delivery_days: entrega real - compra, em dias (fração incluída).
-- delay_days:    entrega real - data estimada (negativo = antecipado).
-- is_on_time:    entrega real <= data estimada (comparando data e hora).
-- distance_km: média, entre os itens do pedido, da distância em linha reta
--   (Haversine) cliente -> vendedor, usando as coordenadas representativas
--   dos CEPs. Itens sem coordenada são ignorados; NULL se nenhum tiver.
-- seller_id: vendedor do item 1 (referência).
CREATE TABLE IF NOT EXISTS gold.fact_order_delivery (
    order_id                       TEXT PRIMARY KEY,
    customer_id                    TEXT    NOT NULL REFERENCES gold.dim_customer (customer_id),
    seller_id                      TEXT    REFERENCES gold.dim_seller (seller_id),
    purchase_date_key              INTEGER NOT NULL REFERENCES gold.dim_date (date_key),
    order_purchase_timestamp       TIMESTAMP NOT NULL,
    order_delivered_customer_date  TIMESTAMP NOT NULL,
    order_estimated_delivery_date  TIMESTAMP NOT NULL,
    delivery_days                  DOUBLE PRECISION NOT NULL,
    estimated_days                 DOUBLE PRECISION NOT NULL,
    delay_days                     DOUBLE PRECISION NOT NULL,
    is_on_time                     BOOLEAN NOT NULL,
    items_qty                      INTEGER NOT NULL,
    freight_total                  NUMERIC(12, 2) NOT NULL,
    distance_km                    DOUBLE PRECISION,
    _run_id     BIGINT      NOT NULL REFERENCES control.pipeline_runs (run_id),
    _loaded_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_gold_fact_sales_date     ON gold.fact_sales (purchase_date_key);
CREATE INDEX IF NOT EXISTS ix_gold_fact_sales_product  ON gold.fact_sales (product_id);
CREATE INDEX IF NOT EXISTS ix_gold_fact_sales_customer ON gold.fact_sales (customer_id);
CREATE INDEX IF NOT EXISTS ix_gold_fact_payments_type  ON gold.fact_payments (payment_type);
CREATE INDEX IF NOT EXISTS ix_gold_fact_delivery_date  ON gold.fact_order_delivery (purchase_date_key);

-- Contagem de TODOS os pedidos por status (página Logística, gráfico de
-- status). Inclui pedidos sem itens, por isso não sai da fact_sales.
CREATE TABLE IF NOT EXISTS gold.agg_order_status (
    order_status  TEXT PRIMARY KEY,
    orders        INTEGER NOT NULL,
    _run_id     BIGINT      NOT NULL REFERENCES control.pipeline_runs (run_id),
    _loaded_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
