# Imagen de la API. Se construye desde la raíz del monorepo para incluir la
# configuración de la tienda:
#   docker build -f apps/api/Dockerfile -t catalog-api .
FROM python:3.13-slim AS base
COPY --from=ghcr.io/astral-sh/uv:0.11.7 /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    STORE_CONFIG_PATH=/app/config/store.toml
WORKDIR /app

# Dependencias de producción, en una capa que solo cambia con el lockfile.
FROM base AS deps
COPY apps/api/pyproject.toml apps/api/uv.lock apps/api/.python-version ./
RUN uv sync --frozen --no-dev --no-install-project

# Desarrollo: suma las dependencias de dev y recarga al editar.
FROM deps AS dev
RUN uv sync --frozen --no-install-project
COPY apps/api/ ./
COPY config/ ./config/
CMD ["uvicorn", "app.main:create_app", "--factory", "--reload", "--host", "0.0.0.0", "--port", "8000"]

# Producción: solo el código y las dependencias necesarias, sin root.
FROM base AS prod
COPY --from=deps /opt/venv /opt/venv
COPY apps/api/app ./app
COPY apps/api/alembic ./alembic
COPY apps/api/alembic.ini ./
COPY config/ ./config/
RUN useradd --system --uid 10001 api
USER api
EXPOSE 8000
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
