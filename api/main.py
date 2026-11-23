"""
BRAZILIAN E-COMMERCE | API (FastAPI)

Expõe a camada Gold do PostgreSQL para a dashboard.

Rodar (na raiz do projeto, com o .venv ativo):
    uvicorn api.main:app --reload
Documentação interativa: http://127.0.0.1:8000/docs
"""

import sys
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "Scripts"))

from db import get_connection  # noqa: E402  (Scripts/db.py, lê DATABASE_URL do .env)

from . import queries  # noqa: E402

app = FastAPI(
    title="Brazilian E-commerce API",
    description="KPIs e séries da camada Gold (Olist) para a dashboard.",
    version="1.0.0",
)

# API somente leitura, de uso local. A dashboard aberta como arquivo
# (file://) envia Origin "null", por isso liberamos qualquer origem para GET.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

PaymentType = Literal["boleto", "credit_card", "debit_card", "not_defined", "voucher"]


def _clean(value: str | None) -> str | None:
    """Trata string vazia como 'sem filtro' (os <select> da dashboard usam '')."""
    return value or None


@app.get("/api/health", tags=["monitoramento"])
def health():
    """Banco acessível, última execução de cada camada e último resultado de qualidade."""
    try:
        with get_connection() as conn:
            return queries.health(conn)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Banco indisponível: {type(exc).__name__}")


@app.get("/api/filters", tags=["comercial"])
def filters():
    """Opções dos filtros da página Comercial."""
    with get_connection() as conn:
        return queries.filter_options(conn)


@app.get("/api/commercial", tags=["comercial"])
def commercial(
    period: str | None = Query(None, pattern=r"^(\d{4}-\d{2})?$", description="Mês 'AAAA-MM'"),
    state: str | None = Query(None, pattern=r"^([A-Z]{2})?$", description="UF do cliente"),
    category: str | None = Query(None, description="category_name (ex.: beleza_saude, 'Sem categoria')"),
    payment: PaymentType | Literal[""] | None = Query(None, description="Pedidos com ao menos um pagamento deste tipo"),
    top: int = Query(10, ge=1, le=100, description="Quantidade de categorias e estados"),
):
    """KPIs, série mensal, ranking de categorias e estados e participação dos pagamentos."""
    with get_connection() as conn:
        return queries.commercial(conn, _clean(period), _clean(state),
                                  _clean(category), _clean(payment), top)


@app.get("/api/logistics", tags=["logística"])
def logistics(states_limit: int = Query(12, ge=1, le=27)):
    """KPIs de entrega, evolução mensal, estados com menor pontualidade e status dos pedidos."""
    with get_connection() as conn:
        return queries.logistics(conn, states_limit)


@app.get("/api/investigation", tags=["investigação"])
def investigation(states_limit: int = Query(8, ge=1, le=27)):
    """Distância x prazo x frete: Spearman, faixas de distância e de frete, estados com mais atraso."""
    with get_connection() as conn:
        return queries.investigation(conn, states_limit)
