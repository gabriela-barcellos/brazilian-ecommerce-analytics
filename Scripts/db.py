"""
Conexão com o PostgreSQL.

Lê DATABASE_URL do arquivo .env na raiz do projeto (ou de uma variável
de ambiente já definida). Nenhuma credencial fica no código.
"""

import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

# ============================================================
# PROJECT CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


def get_database_url() -> str:
    url = os.getenv("DATABASE_URL")

    if not url:
        raise RuntimeError(
            "DATABASE_URL não definida. Copie .env.example para .env "
            f"e preencha a conexão. Procurado em: {ENV_FILE}"
        )

    return url


def get_connection(autocommit: bool = False) -> psycopg.Connection:
    """Abre uma conexão nova. Use com `with get_connection() as conn:`."""
    return psycopg.connect(get_database_url(), autocommit=autocommit)
