# Contribuir a lscrib

Cómo se trabaja en el repo: modelo de ramas, formato de commits y cómo se publican
las versiones (automático).

---

## 1. Modelo de ramas (trunk-based)

- **`master`** es la **única rama de larga vida**. Siempre debe estar en verde
  (compila, pasa lint/tests) y siempre es "releasable".
- El trabajo se hace en **ramas cortas** que salen de `master`, entran por
  **Pull Request** y se borran al mergear:
  - `feat/...` — funcionalidad nueva.
  - `fix/...` — arreglo de bug.
  - `refactor/...`, `docs/...`, `chore/...`, `ci/...` — limpieza, docs, tooling.
- **No hay `develop` ni `release/*` ni `hotfix/*`.** El versionado y las releases los
  gestiona [release-please](#4-releases-automáticas) sobre `master`.

## 2. Repo público (fork & PR)

Colaboradores externos: **fork & pull request**. Haces fork, creas una rama en tu
fork, y abres un PR hacia `master`. La CI corre y el mantenedor revisa.

## 3. Conventional Commits

Los mensajes de commit siguen [Conventional Commits](https://www.conventionalcommits.org/)
**en inglés**. El tipo determina el salto de versión:

- `feat:` → minor (0.**x**.0)
- `fix:` → patch (0.0.**x**)
- `feat!:` / `fix!:` o un footer `BREAKING CHANGE:` → major
- `docs:`, `chore:`, `refactor:`, `style:`, `test:`, `ci:` → no cambian versión

Con scope opcional: `feat(web): ...`, `fix(api): ...`.

## 4. Releases automáticas

[release-please](https://github.com/googleapis/release-please) mantiene un **"release
PR"** abierto que acumula los cambios y sube la versión en `version.txt`,
`lscrib-web/package.json` y `lscrib-api/pyproject.toml`, más el `CHANGELOG.md`.

Al **mergear ese PR**: se crea el **tag** + la **GitHub Release** y se construye/publica
la imagen Docker multi-arch en **GHCR** (`ghcr.io/<owner>/lscrib`). Ver
[`.github/workflows/release.yml`](.github/workflows/release.yml).

## 5. Desarrollo y CI

Para levantar el proyecto en local, ver el [README](README.md).

La CI ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) corre en cada push/PR
a `master`:
- **web:** `npm ci` · `npm run lint` · `npm run build`.
- **api:** `uv sync` · `uv run pytest` (con ffmpeg instalado).
