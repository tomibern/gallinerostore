# Gallinero Store

Catálogo web responsive (tienda pública + panel admin) donde cada consulta termina en WhatsApp o Instagram. Sin carrito ni pagos. Es el primer cliente de un sistema de catálogo reutilizable que se forkea por cliente.

- Discovery y MVP completo: `docs/discovery.md` (fuente de verdad del alcance, modelo de datos y decisiones técnicas).
- Vocabulario del dominio: `GLOSSARY.md`. Usá esos términos en código, issues y tests.
- Decisiones de arquitectura: `docs/adr/` (se crean a medida que se toman).

## Arquitectura

Monorepo:

- `apps/api`: FastAPI (Python 3.12+, uv, SQLAlchemy 2 async, Alembic, Pydantic v2). Toda la lógica de negocio vive acá.
- `apps/web`: Next.js (App Router, TypeScript, Tailwind, shadcn/ui en el admin). Solo muestra datos y llama a la API; no accede a la base.
- `packages/api-client`: cliente TypeScript generado desde el OpenAPI de la API. No se edita a mano.
- Local: `docker compose` con Postgres y MinIO; `make dev` levanta todo.

## Reglas que no se negocian

- **Núcleo genérico.** En `apps/` no aparece nada de River, camisetas ni Gallinero. Lo específico va en `config/store.toml`, `brand/`, `custom/` o en la base de datos.
- **Capas en la API.** Cada módulo de dominio (`catalog`, `media`, `auth`, `events`, `metrics`, `settings`) tiene router → service → repository. Los routers no tienen lógica.
- **Migraciones.** Nunca se edita una migración de Alembic ya commiteada; siempre se crea una nueva.
- **Textos fuera de los componentes.** Los textos de UI salen del diccionario (es-AR por defecto).
- **Tests primero** cuando se agrega comportamiento (`/tdd`): pytest + httpx en la API, Vitest + Playwright en la web.
- **Sin atribución de Claude** en commits ni PRs: nada de `Co-Authored-By: Claude` ni "Generated with Claude Code". El hook `.githooks/commit-msg` lo quita si se cuela.

## Idioma

Documentación, issues y textos de UI en español rioplatense. Código, nombres de tablas y commits en inglés con Conventional Commits (`feat:`, `fix:`, `chore:`).

## Agent skills

Skills de [mattpocock/skills](https://github.com/mattpocock/skills) copiadas en `.claude/skills/` (ver `docs/agents/skills.md`).

### Issue tracker

Los issues viven en GitHub Issues de `tomibern/gallinerostore` y se manejan con `gh`. See `docs/agents/issue-tracker.md`.

### Triage labels

Las cinco etiquetas por defecto (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: un `GLOSSARY.md` y `docs/adr/` en la raíz. See `docs/agents/domain.md`.
