<div align="center">

# lscrib

**Transcribe audio y video en tu propia máquina. Sin nube, sin cuenta, gratis.**

Arrastra un archivo y obtén un transcript editable con timestamps por palabra;
exporta a SRT, VTT, TXT o Markdown. Todo el cómputo ocurre en tu equipo.

</div>

<!-- TODO: GIF de 8-10s (arrastrar -> texto -> SRT) arriba del todo antes de publicar. -->

---

## Por qué lscrib

Whisper (el reconocedor de voz de OpenAI) es excelente, pero su experiencia no:
las herramientas de línea de comandos son inaccesibles, las apps con buena
interfaz son de pago y solo para Mac, y las webs "gratis" suben tu audio al
servidor de un tercero.

**lscrib es la cara que falta:** una app bonita, libre y multiplataforma que corre
Whisper **enteramente en tu máquina**. Tu audio nunca sale del equipo; la única
llamada a la red es la descarga puntual del modelo desde Hugging Face la primera vez.

## Características

- Arrastrar y soltar cualquier audio o video (mp3, wav, m4a, mp4, mov… normalizado con ffmpeg).
- Detección automática de idioma (99+ idiomas) con opción de forzarlo.
- Selector de modelo (tiny → large-v3) con su compromiso de velocidad, calidad y peso.
- Progreso en vivo vía SSE: el transcript aparece a medida que se escribe.
- Transcript editable con timestamps por palabra; clic en una palabra y el audio salta ahí.
- Exporta a SRT, VTT, TXT y Markdown.
- Cola por lotes: encola varios archivos, reordénalos y cancélalos.
- Modo oscuro, interfaz en español e inglés, atajos de teclado, accesibilidad WCAG AA.

## Stack

- **Backend:** Python 3.12 · FastAPI · [faster-whisper](https://github.com/SYSTRAN/faster-whisper) · SQLModel/SQLite · SSE · uv
- **Frontend:** React 19 · Vite · TypeScript · Tailwind v4 · shadcn/ui
- **Media:** ffmpeg

## Cómo ejecutarlo (dev)

Requiere [uv](https://docs.astral.sh/uv/), Node.js y ffmpeg
(`brew install ffmpeg` / `apt install ffmpeg`).

```bash
# backend  -> http://127.0.0.1:8000
cd lscrib-api && uv run lscrib

# frontend -> http://localhost:5173   (en otra terminal)
cd lscrib-web && npm install && npm run dev
```

> El arranque de un solo comando (`docker compose up`) está en el roadmap.

## Licencia

[MIT](./LICENSE) © 2026 Yeltsin López
