# lscrib-web

Frontend de **lscrib**: la cara de la app. Aquí *la UX es el producto* — el motor
(Whisper) es commodity (ver `../context/01_Idea_y_Vision.md`).

## Stack
React + TypeScript + Vite + Tailwind v4. (shadcn/ui se añade en Fase 2.)

## Desarrollo
```bash
npm install
npm run dev      # http://localhost:5173
```
El dev server hace **proxy** de `/api` y `/health` al backend (`lscrib-api`,
:8000), configurado en `vite.config.ts`. Levanta también `uv run lscrib` en
`../lscrib-api` para ver el indicador "backend: conectado ✓".

## Estado
Scaffold de Fase 0: pantalla inicial con dropzone (placeholder), badge de
privacidad "100% local" y health-check del backend. La dropzone funcional, el
progreso en vivo (SSE), el editor de transcript y los exports llegan en la
Fase 2 (`../context/11_Roadmap.md`).
