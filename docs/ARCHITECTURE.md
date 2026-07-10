# Arquitectura de lscrib

Diseño, decisiones técnicas y trade-offs. Si vienes del [README](../README.md) y
quieres entender *cómo* y *por qué* está construido así, este es el documento.

lscrib transcribe audio y video **enteramente en la máquina del usuario**. No hay
backend compartido ni nube: cada persona levanta su propia instancia. Todo el diseño
sale de tres principios.

## Principios

1. **Local-first radical.** El audio nunca sale del equipo. La única salida de red es
   la descarga puntual del modelo de Whisper la primera vez que se usa. No es una
   limitación: es *la* característica.
2. **Un comando.** `docker compose up` levanta API, worker y frontend en un solo
   contenedor. Sin Postgres, sin Redis, sin cola externa. La simplicidad de operación
   es parte del producto: apunta al self-hoster y al no-técnico.
3. **Honestidad de estado.** La UI nunca miente sobre lo que pasa: el progreso es real
   (llega por el propio pipeline), y un reinicio no deja trabajos "colgados" en falso.

## Topología

Un proceso, un contenedor. FastAPI sirve la API, el worker y el frontend ya compilado.

```
┌───────────────────────────────────────────────────────┐
│  proceso `lscrib`  (un contenedor)                      │
│                                                         │
│  FastAPI ── API REST + SSE de progreso                  │
│    │        └─ sirve el build de React (mismo origen)   │
│    │                                                    │
│  worker (asyncio, en proceso) ── un job a la vez        │
│    ├─ ffmpeg          → normaliza a wav 16 kHz mono     │
│    └─ faster-whisper  → transcribe (CPU / Apple Silicon)│
│                                                         │
│  SQLite (lscrib.db)   → metadatos: jobs, segments       │
│  /data                → medios normalizados             │
│  /models              → caché de modelos Whisper        │
└───────────────────────────────────────────────────────┘
        todo en localhost — nada sale a la red
        (salvo bajar el modelo la 1ª vez)
```

Código (`lscrib-api/src/lscrib/`):

| Módulo | Responsabilidad |
|--------|-----------------|
| `api/` | routers FastAPI, endpoint SSE de progreso, servido del SPA |
| `worker/` | cola en proceso (`asyncio`) y ejecución del job, un job a la vez |
| `media/` | wrapper de ffmpeg (normalización a wav 16 kHz mono) |
| `transcribe/` | wrapper de faster-whisper (segmentos + timestamps por palabra) |
| `models/` | descarga y caché de modelos Whisper |
| `db/` | modelos SQLModel, sesión y migraciones Alembic |
| `domain/` | modelos Pydantic y reglas puras (máquina de estados) |
| `export/` | serialización a SRT, VTT, TXT y Markdown |

## El ciclo de vida de un job

```
UPLOADED → QUEUED → NORMALIZING → TRANSCRIBING → COMPLETED
                          │              │
                          └──────────────┴──→ FAILED / CANCELED
```

1. **Subida.** Al recibir un archivo se calcula su **SHA-256**. Si ya existe un job con
   ese hash, se reutiliza en vez de reprocesar — idempotencia gratis y sin duplicar
   trabajo pesado.
2. **Normalización.** ffmpeg convierte cualquier formato a wav 16 kHz mono, la entrada
   que espera Whisper.
3. **Transcripción.** faster-whisper produce segmentos con timestamps **por palabra**.
   El progreso se emite en vivo por **SSE**, y el transcript aparece a medida que se
   escribe. Las palabras de baja confianza se marcan para acelerar la revisión.
4. **Persistencia.** Cada segmento se guarda con su ventana temporal; los timestamps por
   palabra van como JSON en la propia fila (evita una tabla `word` enorme).
5. **Recuperación.** Al arrancar, cualquier job que quedó `in-progress` tras un reinicio
   se marca `FAILED` con un mensaje claro (no hay worker que lo continúe). El usuario lo
   reintenta cuando quiera. La UI no muestra un progreso que ya no avanza.

La cola es reordenable y los jobs se pueden cancelar o borrar; el worker procesa **uno a
la vez** a propósito (ver más abajo).

## Decisiones y trade-offs

**faster-whisper, no `openai-whisper` ni whisper.cpp.** faster-whisper (sobre
CTranslate2) es ~4× más rápido y usa menos RAM que la implementación de referencia, corre
en CPU y aprovecha Apple Silicon, y **se mantiene 100% en Python** — clave para que el
proyecto sea un solo lenguaje en el backend. whisper.cpp (C++) daría otro mundo de build;
se reserva como backend intercambiable si algún día hace falta exprimir la GPU.

**Worker en proceso (`asyncio`), no Celery/Redis.** El requisito es "un job a la vez": un
worker dentro del propio proceso basta y elimina una dependencia de infraestructura
entera. Menos piezas = el "un comando" sigue siendo un comando. Si el roadmap pidiera
concurrencia real, se migra a RQ/Celery sin tocar el dominio.

**SSE, no WebSockets.** El progreso es unidireccional (servidor → cliente). SSE es HTTP
plano, reconecta solo y es trivial de servir. WebSockets solo se justificaría con
colaboración bidireccional, que hoy no existe.

**SQLite, no Postgres.** Metadatos de jobs y segmentos en un archivo, cero setup. Para una
app mono-usuario local es la elección correcta; Postgres sería operación y complejidad sin
beneficio. El acceso es de un solo proceso, con `check_same_thread=False` y timeout para
que API y worker compartan el engine sin pelearse.

**Migraciones con Alembic, no `create_all`.** `create_all` crea tablas nuevas pero **no
altera** las existentes, así que al evolucionar el esquema un usuario que actualiza
perdería columnas nuevas o rompería. Alembic lleva la base a `head` **sola al arrancar**;
las bases creadas antes de introducir migraciones se marcan (stamp) en la baseline sin
recrearse. El usuario nunca corre un comando de migración: actualizar la imagen y reiniciar
basta, y sus datos (en el volumen) sobreviven.

**Un contenedor, no dos.** El build de React se copia dentro de la imagen y FastAPI lo
sirve desde el mismo origen. Nada de CORS en producción, nada de orquestar dos servicios:
un `docker compose up` y listo.

**Sin Tauri / sin desktop en el MVP.** Tauri arrastra Rust por debajo; la web-app local
cubre las tres plataformas con una fracción del esfuerzo. El empaquetado desktop (doble
clic para el no-técnico) se evalúa como paso posterior, no como requisito de lanzamiento.

## Datos y persistencia

Tres tablas (SQLModel): `job` (archivo + estado + progreso + posición en cola), `segment`
(texto editable + ventana temporal + palabras como JSON) y `settings` (fila única de
preferencias). Los medios normalizados viven en `/data` y los modelos en `/models`; ambos
son volúmenes, **independientes de la imagen**, así que actualizar no toca los datos.

## Seguridad y red

La superficie de red saliente del MVP se limita a **descargar el modelo** desde Hugging
Face la primera vez. No hay telemetría, ni cuentas, ni terceros. Al ser mono-usuario y
local, el modelo de amenazas es el de una app de escritorio: quien controla la máquina
controla los datos.

## Qué queda fuera (a propósito) y qué podría venir

El MVP es deliberadamente enfocado: **mono-usuario, sin login, sin multi-cuenta**. Eso
mantiene el diseño simple y fiel al local-first. Son extensiones naturales para la
comunidad, no deuda:

- **Autenticación / multi-usuario** para equipos que self-hostean, cuidando no romper el
  aislamiento local.
- **Diarización de hablantes** y **resúmenes con un LLM local** (p. ej. Ollama).
- **Empaquetado desktop** de doble clic para el público no-técnico.
- **Concurrencia** (varios jobs en paralelo) migrando el worker a una cola externa.

El diseño deja la puerta abierta a todas: el dominio es puro, el worker está aislado y el
esquema evoluciona con migraciones.
