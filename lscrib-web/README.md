# lscrib-web

Frontend de **lscrib**: la cara de la app. Aquí la UX es el producto — el motor
(Whisper) corre en el backend.

## Stack
React 19 · TypeScript · Vite · Tailwind v4 · shadcn/ui

## Desarrollo
```bash
npm install
npm run dev      # http://localhost:5173
npm run build    # build de producción
```
El dev server hace **proxy** de `/api` y `/health` al backend (`lscrib-api`, :8000),
configurado en `vite.config.ts`. Levanta también `uv run lscrib` en `../lscrib-api`
para tener el backend conectado.

En producción, FastAPI sirve el build estático desde el mismo origen (un solo
contenedor). Ver el [README raíz](../README.md).
