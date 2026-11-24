# Imagem única para o pipeline e para a API.
FROM python:3.14-slim

# Sem .pyc e com logs aparecendo na hora (docker compose logs)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependências primeiro: a camada fica em cache enquanto o código muda
COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

# Só o que o pipeline e a API usam (CSVs entram por volume, não pela imagem)
COPY Scripts/ Scripts/
COPY sql/ sql/
COPY api/ api/

# Usuário sem privilégios de administrador
RUN useradd --create-home appuser
USER appuser

# Padrão: API. O serviço "pipeline" sobrescreve este comando.
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
