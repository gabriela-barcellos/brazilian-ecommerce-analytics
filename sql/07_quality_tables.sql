-- ============================================================
-- BRAZILIAN E-COMMERCE | 07 - RESULTADOS DE QUALIDADE
-- Uma linha por verificação, por execução do Scripts/quality_checks.py.
--   severity = 'critical' -> se falhar, o pipeline falha
--   severity = 'warning'  -> registrado, não interrompe
-- Idempotente.
-- ============================================================

CREATE TABLE IF NOT EXISTS control.quality_results (
    result_id   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id      BIGINT      NOT NULL REFERENCES control.pipeline_runs (run_id),
    layer       TEXT        NOT NULL CHECK (layer IN ('bronze', 'silver', 'gold')),
    check_name  TEXT        NOT NULL,
    severity    TEXT        NOT NULL CHECK (severity IN ('critical', 'warning')),
    expected    TEXT,
    observed    TEXT,
    passed      BOOLEAN     NOT NULL,
    checked_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_quality_results_run
    ON control.quality_results (run_id);
