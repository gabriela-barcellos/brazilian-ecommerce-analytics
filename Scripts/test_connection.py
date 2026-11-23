"""
Teste da Etapa 2: Python consegue falar com o PostgreSQL
e enxerga a estrutura criada na Etapa 1.
"""

from db import get_connection

EXPECTED_SCHEMAS = {"bronze", "silver", "gold", "control"}
EXPECTED_TABLES = {
    "bronze": {
        "category_translation", "customers", "geolocation",
        "order_items", "order_payments", "order_reviews",
        "orders", "products", "sellers",
    },
    "control": {"dataset_loads", "pipeline_runs"},
}


def test_connection():

    print("=" * 60)
    print("BRAZILIAN E-COMMERCE | DATABASE CONNECTION TEST")
    print("=" * 60)

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute("SELECT current_database(), current_user, version()")
            database, user, version = cur.fetchone()
            print(f"\nBanco:   {database}")
            print(f"Usuário: {user}")
            print(f"Versão:  {version.split(',')[0]}")

            cur.execute(
                """
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name = ANY(%s)
                """,
                (list(EXPECTED_SCHEMAS),),
            )
            schemas = {row[0] for row in cur.fetchall()}

            cur.execute(
                """
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_schema IN ('bronze', 'control')
                """
            )
            tables = {}
            for schema, table in cur.fetchall():
                tables.setdefault(schema, set()).add(table)

    errors = []

    missing_schemas = EXPECTED_SCHEMAS - schemas
    if missing_schemas:
        errors.append(f"Schemas ausentes: {sorted(missing_schemas)}")

    for schema, expected in EXPECTED_TABLES.items():
        missing = expected - tables.get(schema, set())
        if missing:
            errors.append(f"Tabelas ausentes em {schema}: {sorted(missing)}")

    print(f"\nSchemas encontrados: {sorted(schemas)}")
    for schema in EXPECTED_TABLES:
        print(f"Tabelas em {schema}: {len(tables.get(schema, set()))}")

    print("\n" + "=" * 60)
    if errors:
        for error in errors:
            print(f"FALHA: {error}")
        print("=" * 60)
        raise SystemExit(1)

    print("CONNECTION TEST PASSED")
    print("=" * 60)


if __name__ == "__main__":
    test_connection()
