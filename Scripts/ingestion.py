"""
BRAZILIAN E-COMMERCE | BRONZE INGESTION

Carrega os 9 CSVs da Olist (data/raw) nas tabelas bronze.* do PostgreSQL.

Estratégia de recarga: truncate-and-reload por dataset, dentro de uma
transação. Se um dataset falhar, a tabela dele volta ao estado anterior
(nada fica pela metade) e a execução é marcada como 'failed'.

Fidelidade: o CSV é enviado ao banco via COPY sem passar pelo Pandas,
então os valores chegam exatamente como estão no arquivo (texto).
Valores vazios viram NULL.

Auditoria:
  control.pipeline_runs  -> 1 linha por execução
  control.dataset_loads  -> 1 linha por dataset (linhas no CSV x no banco)
"""

import csv
import sys
from pathlib import Path

from db import get_connection

# ============================================================
# PROJECT CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"

PIPELINE_NAME = "bronze_ingestion"

# dataset -> arquivo CSV (a tabela de destino é bronze.<dataset>)
DATASETS = {
    "customers": "olist_customers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}

METADATA_COLUMNS = {"_ingested_at", "_source_file", "_run_id"}

# Campos de review podem ser longos; o padrão do módulo csv é 128 KB.
csv.field_size_limit(sys.maxsize if sys.maxsize < 2**31 else 2**31 - 1)


# ============================================================
# HELPERS
# ============================================================

def read_csv_header_and_count(file_path: Path):
    """Lê o cabeçalho e conta as linhas de dados (respeita quebras de linha entre aspas).

    utf-8-sig remove o BOM (\ufeff) que alguns CSVs trazem no início,
    ex.: product_category_name_translation.csv. No COPY o BOM não afeta,
    porque a linha de cabeçalho é descartada (HEADER true).
    """
    with open(file_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = [col.strip() for col in next(reader)]
        row_count = sum(1 for _ in reader)
    return header, row_count


def get_table_columns(cur, table: str):
    cur.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'bronze' AND table_name = %s
        ORDER BY ordinal_position
        """,
        (table,),
    )
    return [row[0] for row in cur.fetchall()]


def quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


# ============================================================
# LOAD ONE DATASET
# ============================================================

def load_dataset(conn, run_id: int, dataset: str, filename: str):

    file_path = RAW_DIR / filename
    table = f"bronze.{dataset}"

    if not file_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

    # Registro de auditoria do dataset
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO control.dataset_loads
                (run_id, layer, dataset_name, target_table, source_file)
            VALUES (%s, 'bronze', %s, %s, %s)
            RETURNING load_id
            """,
            (run_id, dataset, table, filename),
        )
        load_id = cur.fetchone()[0]

    try:
        header, rows_source = read_csv_header_and_count(file_path)

        with conn.transaction():
            with conn.cursor() as cur:

                # 1. Cabeçalho do CSV deve bater com as colunas da tabela
                table_columns = [
                    c for c in get_table_columns(cur, dataset)
                    if c not in METADATA_COLUMNS
                ]
                if set(header) != set(table_columns):
                    raise ValueError(
                        f"Colunas do CSV não batem com {table}. "
                        f"Só no CSV: {sorted(set(header) - set(table_columns))} | "
                        f"Só na tabela: {sorted(set(table_columns) - set(header))}"
                    )

                cols = ", ".join(quote_ident(c) for c in header)

                # 2. Recarga completa
                cur.execute(f"TRUNCATE TABLE {table}")

                # 3. COPY para uma tabela temporária (só colunas de origem)
                cur.execute(
                    f"""
                    CREATE TEMP TABLE _stage ON COMMIT DROP AS
                    SELECT {cols} FROM {table} WITH NO DATA
                    """
                )
                with open(file_path, "rb") as f:
                    with cur.copy(
                        f"COPY _stage ({cols}) FROM STDIN "
                        "WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')"
                    ) as copy:
                        while chunk := f.read(1024 * 1024):
                            copy.write(chunk)

                # 4. Bronze = dados de origem + metadados
                cur.execute(
                    f"""
                    INSERT INTO {table} ({cols}, _source_file, _run_id)
                    SELECT {cols}, %s, %s FROM _stage
                    """,
                    (filename, run_id),
                )

                # 5. Reconciliação CSV x banco
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                rows_loaded = cur.fetchone()[0]

                if rows_loaded != rows_source:
                    raise ValueError(
                        f"Contagem divergente em {table}: "
                        f"CSV={rows_source:,} banco={rows_loaded:,}"
                    )

        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE control.dataset_loads
                SET status = 'success', rows_source = %s, rows_loaded = %s,
                    finished_at = now()
                WHERE load_id = %s
                """,
                (rows_source, rows_loaded, load_id),
            )

        print(f"  OK   {dataset:<22} CSV={rows_source:>10,}  banco={rows_loaded:>10,}")
        return rows_loaded

    except Exception as exc:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE control.dataset_loads
                SET status = 'failed', finished_at = now(), error_message = %s
                WHERE load_id = %s
                """,
                (str(exc), load_id),
            )
        print(f"  FAIL {dataset:<22} {exc}")
        raise


# ============================================================
# BRONZE INGESTION
# ============================================================

def ingest_bronze():

    print("=" * 60)
    print("BRAZILIAN E-COMMERCE | BRONZE INGESTION")
    print("=" * 60)

    # autocommit=True: a auditoria é gravada mesmo se um dataset falhar;
    # cada carga roda dentro de sua própria transação (conn.transaction()).
    with get_connection(autocommit=True) as conn:

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO control.pipeline_runs (pipeline_name, layer)
                VALUES (%s, 'bronze')
                RETURNING run_id
                """,
                (PIPELINE_NAME,),
            )
            run_id = cur.fetchone()[0]

        print(f"\nrun_id: {run_id}\n")

        try:
            total = 0
            for dataset, filename in DATASETS.items():
                total += load_dataset(conn, run_id, dataset, filename)

        except Exception as exc:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE control.pipeline_runs
                    SET status = 'failed', finished_at = now(), error_message = %s
                    WHERE run_id = %s
                    """,
                    (str(exc), run_id),
                )
            print("\n" + "=" * 60)
            print(f"BRONZE INGESTION FAILED (run_id {run_id})")
            print("=" * 60)
            raise SystemExit(1)

        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE control.pipeline_runs
                SET status = 'success', finished_at = now()
                WHERE run_id = %s
                """,
                (run_id,),
            )

    print("\n" + "=" * 60)
    print("BRONZE INGESTION COMPLETED SUCCESSFULLY")
    print(f"run_id: {run_id} | datasets: {len(DATASETS)} | linhas: {total:,}")
    print("=" * 60)

    return run_id


# ============================================================
# EXECUTION
# ============================================================

if __name__ == "__main__":
    ingest_bronze()
