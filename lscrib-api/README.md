# lscrib-api

Backend de **lscrib**: API local-first de transcripción de audio/video con Whisper
(`faster-whisper`). El audio nunca sale de la máquina.

## Stack
Python 3.12 · FastAPI · Pydantic v2 · SQLModel (SQLite) · Alembic · faster-whisper · SSE · ffmpeg

## Requisitos
- [`uv`](https://docs.astral.sh/uv/) (gestor de Python)
- `ffmpeg` en el PATH: `brew install ffmpeg` / `apt install ffmpeg`

## Desarrollo
```bash
uv sync          # crea el venv (Python 3.12) e instala dependencias
uv run lscrib    # levanta la API en http://127.0.0.1:8000
uv run pytest    # suite de tests
```
Comprobar: `curl http://127.0.0.1:8000/health` → `{"status":"ok",...}`.
Docs OpenAPI automáticas en `http://127.0.0.1:8000/docs`.

## Estructura (`src/lscrib/`)
| Paquete | Responsabilidad |
|---|---|
| `domain/` | enums + esquemas Pydantic + máquina de estados (puro, testeable) |
| `api/` | app FastAPI, rutas de jobs, endpoints SSE |
| `worker/` | cola en proceso (asyncio): un job a la vez |
| `media/` | wrapper de ffmpeg → wav 16 kHz mono |
| `transcribe/` | wrapper de faster-whisper → segmentos con timestamps |
| `db/` | tablas SQLModel, sesión SQLite y migraciones Alembic |
| `models/` | catálogo y caché de modelos Whisper |
| `export/` | serialización a SRT, VTT, TXT y Markdown |

El esquema lo versiona Alembic y se migra solo al arrancar. Ver
[../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) para el diseño y los trade-offs.
