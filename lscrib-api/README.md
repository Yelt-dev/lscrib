# lscrib-api

Backend de **lscrib**: API local-first de transcripción de audio/video con Whisper
(`faster-whisper`). El audio nunca sale de la máquina (R1).

## Stack
Python 3.12 · FastAPI · Pydantic v2 · SQLModel (SQLite) · faster-whisper · SSE · ffmpeg

## Requisitos
- [`uv`](https://docs.astral.sh/uv/) (gestor de Python)
- `ffmpeg` en el PATH (runtime): `brew install ffmpeg` / `apt install ffmpeg`

## Desarrollo
```bash
uv sync          # crea el venv (Python 3.12) e instala dependencias
uv run lscrib    # levanta la API en http://127.0.0.1:8000
```
Comprobar: `curl http://127.0.0.1:8000/health` → `{"status":"ok",...}`
Docs OpenAPI automáticas en `http://127.0.0.1:8000/docs`.

## Estructura (`src/lscrib/`)
| Paquete | Responsabilidad |
|---|---|
| `domain/` | enums + esquemas Pydantic + máquina de estados (puro, testeable) |
| `api/` | app FastAPI, rutas de jobs, endpoints SSE |
| `worker/` | cola en proceso (asyncio), un trabajo a la vez (R7) |
| `media/` | wrapper de ffmpeg → wav 16 kHz mono (R6) |
| `transcribe/` | wrapper de faster-whisper → segmentos con timestamps |
| `db/` | tablas SQLModel + sesión SQLite |
| `models/` | catálogo y caché de modelos Whisper (R5) |

## Estado
Scaffold de Fase 0. Las rutas y el worker son **stubs** (`NotImplementedError`)
con TODOs que apuntan a la Fase 1 del roadmap (`../context/11_Roadmap.md`).
