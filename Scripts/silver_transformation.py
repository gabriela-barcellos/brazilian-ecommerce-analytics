"""
BRAZILIAN E-COMMERCE | SILVER TRANSFORMATION (Bronze -> Silver)

Executa os SQLs de sql/silver/ em ordem (01_, 02_, ...). Cada arquivo
carrega uma tabela silver.<nome> a partir de bronze.<nome>.

Estratégia: tudo em UMA transação.
  1. TRUNCATE de todas as tabelas Silver
  2. INSERT ... SELECT com tipagem e padronização (arquivos .sql)
  3. Reconciliação: Silver deve ter a mesma contagem da Bronze
Se qualquer passo falhar (cast inválido, PK duplicada, FK órfã, CHECK,
contagem divergente), nada é gravado e a Silver anterior permanece.

Auditoria em control.pipeline_runs / control.dataset_loads, gravada por
uma segunda conexão para sobreviver ao rollback.
"""

from pathlib import Path

from db import get_connection

# ============================================================
# PROJECT CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
SILVER_SQL_DIR = BASE_DIR / "sql" / "silver"

PIPELINE_NAME = "silver_transformation"


def table_from_file(sql_file: Path) -> str:
    """'05_orders.sql' -> 'orders'"""
    return sql_file.stem.split("_", 1)[1]


# ============================================================
# AUDIT HELPERS (conexão autocommit)
# ============================================================

def start_run(audit) -> int:
    with audit.cursor() as cur:
        cur.execute(
            "INSERT INTO control.pipeline_runs (pipeline_name, layer) "
            "VALUES (%s, 'silver') RETURNING run_id",
            (PIPELINE_NAME,),
        )
        return cur.fetchone()[0]


def finish_run(audit, run_id: int, status: str, error: str | None = None):
    with audit.cursor() as cur:
        cur.execute(
            "UPDATE control.pipeline_runs "
            "SET status = %s, finished_at = now(), error_message = %s "
            "WHERE run_id = %s",
            (status, error, run_id),
        )


def log_load(audit, run_id, table, sql_file, rows_source, rows_loaded, status, error=None):
    with audit.cursor() as cur:
        cur.execute(
            """
            INSERT INTO control.dataset_loads
                (run_id, layer, dataset_name, target_table, source_file,
                 rows_source, rows_loaded, status, finished_at, error_message)
            VALUES (%s, 'silver', %s, %s, %s, %s, %s, %s, now(), %s)
            """,
            (run_id, table, f"silver.{table}", f"sql/silver/{sql_file.name}",
             rows_source, rows_loaded, status, error),
        )


# ============================================================
# SILVER TRANSFORMATION
# ============================================================

def transform_silver():

    print("=" * 60)
    print("BRAZILIAN E-COMMERCE | SILVER TRANSFORMATION")
    print("=" * 60)

    sql_files = sorted(SILVER_SQL_DIR.glob("[0-9][0-9]_*.sql"))
    if not sql_files:
        raise FileNotFoundError(f"Nenhum SQL encontrado em {SILVER_SQL_DIR}")

    tables = [table_from_file(f) for f in sql_files]

    with get_connection(autocommit=True) as audit, get_connection() as conn:

        run_id = start_run(audit)
        print(f"\nrun_id: {run_id}\n")

        results = []
        current = None

        try:
            with conn.cursor() as cur:

                # 1. Limpa todas as tabelas de uma vez (respeita as FKs)
                cur.execute(
                    "TRUNCATE TABLE "
                    + ", ".join(f"silver.{t}" for t in tables)
                )

                # 2. Carga em ordem de dependência
                for sql_file, table in zip(sql_files, tables):
                    current = (sql_file, table)

                    cur.execute(sql_file.read_text(encoding="utf-8"), {"run_id": run_id})

                    cur.execute(f"SELECT COUNT(*) FROM bronze.{table}")
                    rows_source = cur.fetchone()[0]
                    cur.execute(f"SELECT COUNT(*) FROM silver.{table}")
                    rows_loaded = cur.fetchone()[0]

                    # 3. Reconciliação: a Silver não descarta linhas
                    if rows_loaded != rows_source:
                        raise ValueError(
                            f"Contagem divergente em silver.{table}: "
                            f"bronze={rows_source:,} silver={rows_loaded:,}"
                        )

                    results.append((sql_file, table, rows_source, rows_loaded))
                    print(f"  OK   {table:<22} bronze={rows_source:>10,}  silver={rows_loaded:>10,}")

            conn.commit()

        except Exception as exc:
            conn.rollback()
            error = f"{type(exc).__name__}: {exc}".strip()

            if current:
                sql_file, table = current
                print(f"  FAIL {table:<22} {error}")
                log_load(audit, run_id, table, sql_file, None, None, "failed", error)

            finish_run(audit, run_id, "failed", error)
            print("\n" + "=" * 60)
            print(f"SILVER TRANSFORMATION FAILED (run_id {run_id})")
            print("Nada foi gravado: a Silver anterior foi mantida.")
            print("=" * 60)
            raise SystemExit(1)

        for sql_file, table, rows_source, rows_loaded in results:
            log_load(audit, run_id, table, sql_file, rows_source, rows_loaded, "success")
        finish_run(audit, run_id, "success")

    total = sum(r[3] for r in results)
    print("\n" + "=" * 60)
    print("SILVER TRANSFORMATION COMPLETED SUCCESSFULLY")
    print(f"run_id: {run_id} | tabelas: {len(results)} | linhas: {total:,}")
    print("=" * 60)

    return run_id


# ============================================================
# EXECUTION
# ============================================================

if __name__ == "__main__":
    transform_silver()
