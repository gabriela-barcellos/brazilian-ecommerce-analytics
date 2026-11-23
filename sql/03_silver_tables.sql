-- ============================================================
-- BRAZILIAN E-COMMERCE | 03 - TABELAS SILVER
-- Dados tipados, padronizados e com chaves explícitas.
-- Idempotente: pode ser executado mais de uma vez.
--
-- Regras gerais da Silver
--   * Nenhuma linha é excluída: Silver tem a mesma contagem da Bronze.
--   * Nulos são preservados (não há imputação).
--   * Texto: trim; cidade e categoria em minúsculas; UF em maiúsculas.
--   * CEP (prefixo) fica como TEXTO de 5 dígitos para não perder o zero
--     à esquerda (ex.: '09790').
--   * Restrições (PK, FK, CHECK) só para regras CRÍTICAS. Se forem
--     violadas, a carga falha. Casos apenas suspeitos (pagamento zero,
--     0 parcelas, frete zero...) são aceitos e reportados na validação.
--   * Colunas com erro de digitação na origem foram corrigidas:
--     product_name_lenght -> product_name_length
--     product_description_lenght -> product_description_length
-- ============================================================

CREATE TABLE IF NOT EXISTS silver.category_translation (
    product_category_name          TEXT PRIMARY KEY,
    product_category_name_english  TEXT NOT NULL,
    _run_id     BIGINT      NOT NULL REFERENCES control.pipeline_runs (run_id),
    _loaded_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS silver.customers (
    customer_id               TEXT PRIMARY KEY,
    customer_unique_id        TEXT NOT NULL,
    customer_zip_code_prefix  TEXT NOT NULL CHECK (customer_zip_code_prefix ~ '^[0-9]{5}$'),
    customer_city             TEXT NOT NULL,
    customer_state            CHAR(2) NOT NULL,
    _run_id     BIGINT      NOT NULL REFERENCES control.pipeline_runs (run_id),
    _loaded_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS silver.sellers (
    seller_id               TEXT PRIMARY KEY,
    seller_zip_code_prefix  TEXT NOT NULL CHECK (seller_zip_code_prefix ~ '^[0-9]{5}$'),
    seller_city             TEXT NOT NULL,
    seller_state            CHAR(2) NOT NULL,
    _run_id     BIGINT      NOT NULL REFERENCES control.pipeline_runs (run_id),
    _loaded_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Sem FK para category_translation: 2 categorias da origem não têm tradução
-- (pc_gamer, portateis_cozinha_e_preparadores_de_alimentos). Tratado na Gold.
CREATE TABLE IF NOT EXISTS silver.products (
    product_id                  TEXT PRIMARY KEY,
    product_category_name       TEXT,
    product_name_length         INTEGER CHECK (product_name_length >= 0),
    product_description_length  INTEGER CHECK (product_description_length >= 0),
    product_photos_qty          INTEGER CHECK (product_photos_qty >= 0),
    product_weight_g            INTEGER CHECK (product_weight_g >= 0),
    product_length_cm           INTEGER CHECK (product_length_cm >= 0),
    product_height_cm           INTEGER CHECK (product_height_cm >= 0),
    product_width_cm            INTEGER CHECK (product_width_cm >= 0),
    _run_id     BIGINT      NOT NULL REFERENCES control.pipeline_runs (run_id),
    _loaded_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS silver.orders (
    order_id                       TEXT PRIMARY KEY,
    customer_id                    TEXT NOT NULL REFERENCES silver.customers (customer_id),
    order_status                   TEXT NOT NULL CHECK (order_status IN (
                                       'approved', 'canceled', 'created', 'delivered',
                                       'invoiced', 'processing', 'shipped', 'unavailable')),
    order_purchase_timestamp       TIMESTAMP NOT NULL,
    order_approved_at              TIMESTAMP,
    order_delivered_carrier_date   TIMESTAMP,
    order_delivered_customer_date  TIMESTAMP,
    order_estimated_delivery_date  TIMESTAMP NOT NULL,
    _run_id     BIGINT      NOT NULL REFERENCES control.pipeline_runs (run_id),
    _loaded_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS silver.order_items (
    order_id             TEXT    NOT NULL REFERENCES silver.orders (order_id),
    order_item_id        INTEGER NOT NULL CHECK (order_item_id >= 1),
    product_id           TEXT    NOT NULL REFERENCES silver.products (product_id),
    seller_id            TEXT    NOT NULL REFERENCES silver.sellers (seller_id),
    shipping_limit_date  TIMESTAMP NOT NULL,
    price                NUMERIC(12, 2) NOT NULL CHECK (price > 0),
    freight_value        NUMERIC(12, 2) NOT NULL CHECK (freight_value >= 0),
    _run_id     BIGINT      NOT NULL REFERENCES control.pipeline_runs (run_id),
    _loaded_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (order_id, order_item_id)
);

-- Granularidade diferente de order_items: NÃO juntar direto para somar receita.
CREATE TABLE IF NOT EXISTS silver.order_payments (
    order_id              TEXT    NOT NULL REFERENCES silver.orders (order_id),
    payment_sequential    INTEGER NOT NULL CHECK (payment_sequential >= 1),
    payment_type          TEXT    NOT NULL CHECK (payment_type IN (
                                      'boleto', 'credit_card', 'debit_card', 'not_defined', 'voucher')),
    payment_installments  INTEGER NOT NULL CHECK (payment_installments >= 0),
    payment_value         NUMERIC(12, 2) NOT NULL CHECK (payment_value >= 0),
    _run_id     BIGINT      NOT NULL REFERENCES control.pipeline_runs (run_id),
    _loaded_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (order_id, payment_sequential)
);

-- review_id sozinho NÃO é único na origem (789 IDs repetidos);
-- a chave é (review_id, order_id).
CREATE TABLE IF NOT EXISTS silver.order_reviews (
    review_id                TEXT     NOT NULL,
    order_id                 TEXT     NOT NULL REFERENCES silver.orders (order_id),
    review_score             SMALLINT NOT NULL CHECK (review_score BETWEEN 1 AND 5),
    review_comment_title     TEXT,
    review_comment_message   TEXT,
    review_creation_date     TIMESTAMP NOT NULL,
    review_answer_timestamp  TIMESTAMP NOT NULL,
    _run_id     BIGINT      NOT NULL REFERENCES control.pipeline_runs (run_id),
    _loaded_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (review_id, order_id)
);

-- Sem PK: a origem tem 261.831 linhas duplicadas e várias coordenadas por
-- prefixo de CEP. A coordenada representativa por prefixo é definida na Gold.
-- is_within_brazil marca coordenadas fora do retângulo aproximado do Brasil.
CREATE TABLE IF NOT EXISTS silver.geolocation (
    geolocation_zip_code_prefix  TEXT NOT NULL CHECK (geolocation_zip_code_prefix ~ '^[0-9]{5}$'),
    geolocation_lat              DOUBLE PRECISION NOT NULL,
    geolocation_lng              DOUBLE PRECISION NOT NULL,
    geolocation_city             TEXT NOT NULL,
    geolocation_state            CHAR(2) NOT NULL,
    is_within_brazil             BOOLEAN NOT NULL,
    _run_id     BIGINT      NOT NULL REFERENCES control.pipeline_runs (run_id),
    _loaded_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_silver_geolocation_zip
    ON silver.geolocation (geolocation_zip_code_prefix);
CREATE INDEX IF NOT EXISTS ix_silver_orders_customer
    ON silver.orders (customer_id);
CREATE INDEX IF NOT EXISTS ix_silver_order_items_product
    ON silver.order_items (product_id);
CREATE INDEX IF NOT EXISTS ix_silver_order_items_seller
    ON silver.order_items (seller_id);
