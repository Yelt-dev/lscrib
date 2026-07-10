# syntax=docker/dockerfile:1

# --- 1) Build del frontend (Vite) -------------------------------------------
FROM node:22-slim AS web
WORKDIR /web
COPY lscrib-web/package.json lscrib-web/package-lock.json ./
RUN npm ci
COPY lscrib-web/ ./
RUN npm run build

# --- 2) Runtime del backend (FastAPI + faster-whisper) ----------------------
FROM python:3.12-slim
# ffmpeg es requisito de runtime
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*
# uv (gestor de paquetes)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app
# Dependencias primero (mejor caché): copia manifiestos y sincroniza sin proyecto
COPY lscrib-api/pyproject.toml lscrib-api/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
# Ahora el código del backend y la instalación del propio paquete
COPY lscrib-api/ ./
RUN uv sync --frozen --no-dev
# El build de React que sirve FastAPI
COPY --from=web /web/dist ./static

ENV LSCRIB_HOST=0.0.0.0 \
    LSCRIB_STATIC_DIR=/app/static \
    LSCRIB_DATA_DIR=/data \
    LSCRIB_DB_PATH=/data/lscrib.db \
    HF_HOME=/models

EXPOSE 8000
CMD ["uv", "run", "--no-sync", "lscrib"]
