-- ============================================================
-- BRAZILIAN E-COMMERCE | 01 - POSTGRESQL FOUNDATION
-- Banco: brazilian_ecommerce
-- Cria schemas, tabelas de controle e tabelas Bronze.
-- Idempotente: pode ser executado mais de uma vez.
-- ============================================================

-- ------------------------------------------------------------
-- SCHEMAS
-- ------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS bronze;   -- dados brutos, como vieram do CSV
CREATE SCHEMA IF NOT EXISTS silver;   -- dados tipados, limpos e validados
CREATE SCHEMA IF NOT EXISTS gold;     -- star schema e métricas
CREATE SCHEMA IF NOT EXISTS control;  -- auditoria do pipeline

-- ------------------------------------------------------------
-- CONTROL
-- pipeline_runs : uma linha por execução do pipeline
-- dataset_loads : uma linha por dataset carregado em cada execução
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS control.pipeline_runs (
    run_id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pipeline_name  TEXT        NOT NULL,
    layer          TEXT        NOT NULL CHECK (layer IN ('bronze', 'silver', 'gold', 'quality')),
    status         TEXT        NOT NULL DEFAULT 'running'
                               CHECK (status IN ('running', 'success', 'failed')),
    started_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at    TIMESTAMPTZ,
    error_message  TEXT
);

CREATE TABLE IF NOT EXISTS control.dataset_loads (
    load_id        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id         BIGINT      NOT NULL REFERENCES control.pipeline_runs (run_id),
    layer          TEXT        NOT NULL,
    dataset_name   TEXT        NOT NULL,
    target_table   TEXT        NOT NULL,
    source_file    TEXT,
    rows_source    BIGINT,
    rows_loaded    BIGINT,
    status         TEXT        NOT NULL DEFAULT 'running'
                               CHECK (status IN ('running', 'success', 'failed')),
    started_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at    TIMESTAMPTZ,
    error_message  TEXT
);

-- ------------------------------------------------------------
-- BRONZE
-- Colunas de origem em TEXT para preservar o CSV original
-- (inclusive os erros de digitação "lenght" do dataset Olist).
-- Sem PK: a Bronze não rejeita linhas; validação fica na Silver.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bronze.customers (
    customer_id                TEXT,
    customer_unique_id         TEXT,
    customer_zip_code_prefix   TEXT,
    customer_city              TEXT,
    customer_state             TEXT,
    _ingested_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    _source_file  TEXT        NOT NULL,
    _run_id       BIGINT      NOT NULL REFERENCES control.pipeline_runs (run_id)
);

CREATE TABLE IF NOT EXISTS bronze.geolocation (
    geolocation_zip_code_prefix  TEXT,
    geolocation_lat              TEXT,
    geolocation_lng              TEXT,
    geolocation_city             TEXT,
    geolocation_state            TEXT,
    _ingested_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    _source_file  TEXT        NOT NULL,
    _run_id       BIGINT      NOT NULL REFERENCES control.pipeline_runs (run_id)
);

CREATE TABLE IF NOT EXISTS bronze.order_items (
    order_id             TEXT,
    order_item_id        TEXT,
    product_id           TEXT,
    seller_id            TEXT,
    shipping_limit_date  TEXT,
    price                TEXT,
    freight_value        TEXT,
    _ingested_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    _source_file  TEXT        NOT NULL,
    _run_id       BIGINT      NOT NULL REFERENCES control.pipeline_runs (run_id)
);

CREATE TABLE IF NOT EXISTS bronze.order_payments (
    order_id              TEXT,
    payment_sequential    TEXT,
    payment_type          TEXT,
    payment_installments  TEXT,
    payment_value         TEXT,
    _ingested_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    _source_file  TEXT        NOT NULL,
    _run_id       BIGINT      NOT NULL REFERENCES control.pipeline_runs (run_id)
);

CREATE TABLE IF NOT EXISTS bronze.order_reviews (
    review_id                TEXT,
    order_id                 TEXT,
    review_score             TEXT,
    review_comment_title     TEXT,
    review_comment_message   TEXT,
    review_creation_date     TEXT,
    review_answer_timestamp  TEXT,
    _ingested_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    _source_file  TEXT        NOT NULL,
    _run_id       BIGINT      NOT NULL REFERENCES control.pipeline_runs (run_id)
);

CREATE TABLE IF NOT EXISTS bronze.orders (
    order_id                       TEXT,
    customer_id                    TEXT,
    order_status                   TEXT,
    order_purchase_timestamp       TEXT,
    order_approved_at              TEXT,
    order_delivered_carrier_date   TEXT,
    order_delivered_customer_date  TEXT,
    order_estimated_delivery_date  TEXT,
    _ingested_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    _source_file  TEXT        NOT NULL,
    _run_id       BIGINT      NOT NULL REFERENCES control.pipeline_runs (run_id)
);

CREATE TABLE IF NOT EXISTS bronze.products (
    product_id                  TEXT,
    product_category_name       TEXT,
    product_name_lenght         TEXT,
    product_description_lenght  TEXT,
    product_photos_qty          TEXT,
    product_weight_g            TEXT,
    product_length_cm           TEXT,
    product_height_cm           TEXT,
    product_width_cm            TEXT,
    _ingested_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    _source_file  TEXT        NOT NULL,
    _run_id       BIGINT      NOT NULL REFERENCES control.pipeline_runs (run_id)
);

CREATE TABLE IF NOT EXISTS bronze.sellers (
    seller_id               TEXT,
    seller_zip_code_prefix  TEXT,
    seller_city             TEXT,
    seller_state            TEXT,
    _ingested_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    _source_file  TEXT        NOT NULL,
    _run_id       BIGINT      NOT NULL REFERENCES control.pipeline_runs (run_id)
);

CREATE TABLE IF NOT EXISTS bronze.category_translation (
    product_category_name          TEXT,
    product_category_name_english  TEXT,
    _ingested_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    _source_file  TEXT        NOT NULL,
    _run_id       BIGINT      NOT NULL REFERENCES control.pipeline_runs (run_id)
);
