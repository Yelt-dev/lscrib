# Changelog

## [0.2.0](https://github.com/Yelt-dev/lscrib/compare/v0.1.0...v0.2.0) (2026-07-14)


### Features

* **api:** detect CPUs without SSE4.2 instead of dying with SIGILL ([54c144b](https://github.com/Yelt-dev/lscrib/commit/54c144b63139b3520cd93d9796cb369df45e6b62))
* detect unsupported CPUs, add upload feedback ([852251c](https://github.com/Yelt-dev/lscrib/commit/852251c717693b11b2a8e46446c5485b8a5cbe73))
* **web:** show upload progress and warn on unsupported CPU ([8e3758c](https://github.com/Yelt-dev/lscrib/commit/8e3758ceb88be53bdfbd87b5112b5a4b4148d998))


### Bug Fixes

* **web:** only suggest installing ffmpeg when ffmpeg is missing ([48ad39c](https://github.com/Yelt-dev/lscrib/commit/48ad39c5cd68d6a085e161aa6be02d0f91854e5c))

## 0.1.0 (2026-07-10)


### Features

* **api:** manage schema with Alembic migrations ([ce497ec](https://github.com/Yelt-dev/lscrib/commit/ce497ec5471a9b0e0004e3cce4859a4326feec8b))
* **api:** serve the React build from FastAPI for single-origin production ([f92f8b4](https://github.com/Yelt-dev/lscrib/commit/f92f8b41658887b4230d2cfe864f93b9d69042f7))
* flag low-confidence words to speed up transcript review ([cf70267](https://github.com/Yelt-dev/lscrib/commit/cf70267577393743dceb3b77ef7bbaa97bedf933))
* local-first audio & video transcription app ([5f7f461](https://github.com/Yelt-dev/lscrib/commit/5f7f46168ce803452ef0b2901513dc42c91b9b8f))
* one-command launch with Docker (docker compose up) ([f76b717](https://github.com/Yelt-dev/lscrib/commit/f76b7178d27eb4c86cd7458f8c7ef9bd8db588fd))
* paginate jobs with a scrollable sidebar, load-more and visible queue order ([dd8a538](https://github.com/Yelt-dev/lscrib/commit/dd8a53816a5e7d14ce20b4e423042c12683dffc8))
* vocabulary hint (hotwords) to improve proper nouns and jargon ([4ce1dc2](https://github.com/Yelt-dev/lscrib/commit/4ce1dc20c255442d54cb0ba79b08d1f00244c08c))
* **web:** replace text wordmark with the real logo and favicon ([6004956](https://github.com/Yelt-dev/lscrib/commit/60049563bd62d6603f8014d26d30945ddbdf0934))
* **web:** sticky player, follow-along scroll, transcript search and click-to-edit ([1dffb45](https://github.com/Yelt-dev/lscrib/commit/1dffb455a66d676da05af4607340996f1f047b70))


### Bug Fixes

* **web:** guard against missing paginated response fields ([8ff314a](https://github.com/Yelt-dev/lscrib/commit/8ff314aedd4efed749b9dcc486ffdf648c905819))
* **web:** inset selection ring so it isn't clipped in the jobs sidebar ([9a32bbe](https://github.com/Yelt-dev/lscrib/commit/9a32bbe174cb6f4c5af078c2d5780f84397fa309))
* **web:** sticky header so theme and language stay reachable in long transcripts ([d148b73](https://github.com/Yelt-dev/lscrib/commit/d148b733196db1a9122e22c667b3dc22d615180e))


### Miscellaneous Chores

* cut the first public release as 0.1.0 ([91ba350](https://github.com/Yelt-dev/lscrib/commit/91ba3504c559f4260f4e63cfda8fa718bac61b2c))

## Changelog

Este archivo lo mantiene [release-please](https://github.com/googleapis/release-please)
a partir de los mensajes de commit (Conventional Commits). No lo edites a mano.
