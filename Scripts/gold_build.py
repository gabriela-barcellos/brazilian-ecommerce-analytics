"""
BRAZILIAN E-COMMERCE | GOLD BUILD (Silver -> Gold / Star Schema)

Executa os SQLs de sql/gold/ em ordem. Cada arquivo carrega gold.<nome>.

Estratégia: tudo em UMA transação (mesma lógica da Silver).
  1. TRUNCATE de todas as tabelas Gold
  2. INSERT ... SELECT (arquivos .sql)
  3. Reconciliação Silver x Gold (contagens e somas). Divergência = falha.
Se algo falhar, nada é gravado e a Gold anterior permanece.
"""

from pathlib import Path

from db import get_connection

# ============================================================
# PROJECT CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
GOLD_SQL_DIR = BASE_DIR / "sql" / "gold"

PIPELINE_NAME = "gold_build"

# Tabela Gold -> consulta que dá a contagem esperada na origem (Silver).
SOURCE_COUNTS = {
    "zip_prefix_location": "SELECT COUNT(DISTINCT geolocation_zip_code_prefix) FROM silver.geolocation",
    "dim_date": """SELECT (MAX(order_purchase_timestamp)::DATE
                          - MIN(order_purchase_timestamp)::DATE) + 1 FROM silver.orders""",
    "dim_customer": "SELECT COUNT(*) FROM silver.customers",
    "dim_seller": "SELECT COUNT(*) FROM silver.sellers",
    "dim_product": "SELECT COUNT(*) FROM silver.products",
    "fact_sales": "SELECT COUNT(*) FROM silver.order_items",
    "fact_payments": "SELECT COUNT(*) FROM silver.order_payments",
    "fact_order_delivery": """SELECT COUNT(*) FROM silver.orders
                              WHERE order_status = 'delivered'
                                AND order_delivered_customer_date IS NOT NULL""",
    "agg_order_status": "SELECT COUNT(DISTINCT order_status) FROM silver.orders",
}

# Somas que não podem mudar entre Silver e Gold (proteção contra JOIN duplicando).
SUM_CHECKS = [
    ("receita (price)", "SELECT SUM(price) FROM silver.order_items",
                        "SELECT SUM(price) FROM gold.fact_sales"),
    ("frete", "SELECT SUM(freight_value) FROM silver.order_items",
              "SELECT SUM(freight_value) FROM gold.fact_sales"),
    ("pagamentos", "SELECT SUM(payment_value) FROM silver.order_payments",
                   "SELECT SUM(payment_value) FROM gold.fact_payments"),
]


def table_from_file(sql_file: Path) -> str:
    """'06_fact_sales.sql' -> 'fact_sales'"""
    return sql_file.stem.split("_", 1)[1]


# ============================================================
# AUDIT HELPERS (conexão autocommit)
# ============================================================

def start_run(audit) -> int:
    with audit.cursor() as cur:
        cur.execute(
            "INSERT INTO control.pipeline_runs (pipeline_name, layer) "
            "VALUES (%s, 'gold') RETURNING run_id",
            (PIPELINE_NAME,),
        )
        return cur.fetchone()[0]


def finish_run(audit, run_id, status, error=None):
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
            VALUES (%s, 'gold', %s, %s, %s, %s, %s, %s, now(), %s)
            """,
            (run_id, table, f"gold.{table}", f"sql/gold/{sql_file.name}",
             rows_source, rows_loaded, status, error),
        )


def scalar(cur, sql):
    cur.execute(sql)
    return cur.fetchone()[0]


# ============================================================
# GOLD BUILD
# ============================================================

def build_gold():

    print("=" * 60)
    print("BRAZILIAN E-COMMERCE | GOLD BUILD")
    print("=" * 60)

    sql_files = sorted(GOLD_SQL_DIR.glob("[0-9][0-9]_*.sql"))
    if not sql_files:
        raise FileNotFoundError(f"Nenhum SQL encontrado em {GOLD_SQL_DIR}")

    tables = [table_from_file(f) for f in sql_files]
    missing = set(tables) - set(SOURCE_COUNTS)
    if missing:
        raise ValueError(f"Sem contagem de origem definida para: {sorted(missing)}")

    with get_connection(autocommit=True) as audit, get_connection() as conn:

        run_id = start_run(audit)
        print(f"\nrun_id: {run_id}\n")

        results = []
        current = None

        try:
            with conn.cursor() as cur:

                # 1. Limpa todas as tabelas Gold de uma vez (respeita as FKs)
                cur.execute("TRUNCATE TABLE " + ", ".join(f"gold.{t}" for t in tables))

                # 2. Carga em ordem de dependência + reconciliação de contagem
                for sql_file, table in zip(sql_files, tables):
                    current = (sql_file, table)

                    cur.execute(sql_file.read_text(encoding="utf-8"), {"run_id": run_id})

                    rows_source = scalar(cur, SOURCE_COUNTS[table])
                    rows_loaded = scalar(cur, f"SELECT COUNT(*) FROM gold.{table}")

                    if rows_loaded != rows_source:
                        raise ValueError(
                            f"Contagem divergente em gold.{table}: "
                            f"esperado={rows_source:,} gold={rows_loaded:,}"
                        )

                    results.append((sql_file, table, rows_source, rows_loaded))
                    print(f"  OK   {table:<22} origem={rows_source:>10,}  gold={rows_loaded:>10,}")

                # 3. Somas Silver x Gold
                current = None
                print()
                for name, silver_sql, gold_sql in SUM_CHECKS:
                    silver_value = scalar(cur, silver_sql)
                    gold_value = scalar(cur, gold_sql)
                    if silver_value != gold_value:
                        raise ValueError(
                            f"Soma divergente ({name}): silver={silver_value} gold={gold_value}"
                        )
                    print(f"  OK   soma {name:<17} R$ {gold_value:>15,.2f}")

            conn.commit()

        except Exception as exc:
            conn.rollback()
            error = f"{type(exc).__name__}: {exc}".strip()

            if current:
                sql_file, table = current
                print(f"  FAIL {table:<22} {error}")
                log_load(audit, run_id, table, sql_file, None, None, "failed", error)
            else:
                print(f"  FAIL {error}")

            finish_run(audit, run_id, "failed", error)
            print("\n" + "=" * 60)
            print(f"GOLD BUILD FAILED (run_id {run_id})")
            print("Nada foi gravado: a Gold anterior foi mantida.")
            print("=" * 60)
            raise SystemExit(1)

        for sql_file, table, rows_source, rows_loaded in results:
            log_load(audit, run_id, table, sql_file, rows_source, rows_loaded, "success")
        finish_run(audit, run_id, "success")

    print("\n" + "=" * 60)
    print("GOLD BUILD COMPLETED SUCCESSFULLY")
    print(f"run_id: {run_id} | tabelas: {len(results)}")
    print("=" * 60)

    return run_id


# ============================================================
# EXECUTION
# ============================================================

if __name__ == "__main__":
    build_gold()
