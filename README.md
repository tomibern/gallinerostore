# Gallinero Store

Catálogo web de indumentaria de fútbol donde cada consulta termina en WhatsApp o Instagram. Monorepo con API en FastAPI y frontend en Next.js.

- Alcance, modelo de datos y decisiones: [docs/discovery.md](docs/discovery.md)
- Glosario: [GLOSSARY.md](GLOSSARY.md)
- Decisiones de arquitectura: [docs/adr/](docs/adr/)
- Cómo trabajo con agentes: [docs/agents/skills.md](docs/agents/skills.md)

## Estructura

| Carpeta | Qué hay |
|---|---|
| `apps/api` | API en FastAPI (Python 3.13, uv). Toda la lógica de negocio. |
| `apps/web` | Web en Next.js. Muestra datos y habla con la API a través de `/api`. |
| `packages/api-client` | Cliente TypeScript de la API, generado desde su OpenAPI (`make gen-client`). No se edita a mano. |
| `config/store.toml` | Datos de la tienda del cliente: nombre, moneda, prefijo de código, features. |
| `config/seed.toml` | Datos iniciales del cliente: talles, categorías, colecciones, versiones y productos de prueba. |
| `brand/<marca>/` | Tokens de color y recursos de la marca. Pisa el tema neutro del núcleo. |
| `docker-compose.yml` | Postgres y almacenamiento S3 (RustFS) para desarrollo. |

En `apps/` no aparece nada específico del cliente (ADR 0001).

## Requisitos

- Docker con Compose
- [uv](https://docs.astral.sh/uv/) (instala Python 3.13 solo)
- Node 22 (`nvm use`)
- GNU Make

## Primer arranque

```bash
git clone git@github.com:tomibern/gallinerostore.git
```

```bash
cd gallinerostore
```

```bash
make hooks
```

```bash
cp .env.example .env
```

```bash
make dev
```

`make dev` instala dependencias, levanta Postgres y el almacenamiento, espera a que estén sanos, aplica las migraciones, crea el bucket de imágenes y arranca la API y la web con recarga automática. `Ctrl+C` corta todo. `make test` crea la base de tests si hace falta.

Los tests de la API también crean y migran su base solos. En un worktree de git, la base y el bucket de tests llevan el nombre del worktree como sufijo (`gallinero_test_<worktree>`, `test-media-<worktree>`), así varios worktrees pueden correr la suite en paralelo sin bloquearse ni borrarse las imágenes. Esas bases no se borran solas cuando se elimina el worktree.

Para tener productos de prueba:

```bash
make seed
```

Se puede correr las veces que haga falta: actualiza lo que ya existe sin duplicar. Cada producto sin fotos recibe una imagen de prueba, subida al almacenamiento y servida en `/media`.

Si `.env` tiene `SEED_ADMIN_EMAIL` y `SEED_ADMIN_PASSWORD` (están en `.env.example`), el seed también crea un admin de prueba para entrar al panel en <http://localhost:3000/admin>. El e2e entra con él.

Con `make dev` y `make seed` corriendo, el test de punta a punta (Playwright, escritorio y celular):

```bash
make e2e
```

Para que ningún test se saltee, levantá todo así:

```bash
LISTING_PAGE_SIZE=3 RATE_LIMIT_ENABLED=false E2E_ENDPOINTS=true make dev
```

- `LISTING_PAGE_SIZE` (de 1 a 20; 20 por defecto): los tests del scroll infinito necesitan más de una página de productos, y el seed tiene pocos.
- `RATE_LIMIT_ENABLED=false`: todo el e2e sale de la misma IP y pasaría el límite de frecuencia de los eventos y el de intentos fallidos de login.
- `E2E_ENDPOINTS=true`: habilita `GET /e2e/events`, con el que el e2e verifica que una visita y una consulta quedaron guardadas. Nunca en producción.

La primera vez hay que bajar el navegador: `npx playwright install chromium`.

- Web: <http://localhost:3000>
- Desde el celular (misma wifi): `http://<ip-de-la-compu>:3000` (`make dev` la imprime al arrancar)
- API directa: <http://localhost:8000/docs>
- Consola del almacenamiento: <http://localhost:9001>

Postgres se publica en el puerto 5433 para no chocar con un Postgres instalado en la máquina.

## Calidad

- **Hooks de git** (`make hooks`, una vez por clon): antes de cada commit corren ruff, mypy, Prettier y ESLint sobre los archivos cambiados; si algo falla, el commit no se crea. En el mensaje se quita cualquier atribución de Claude.
- **CI** (GitHub Actions, `.github/workflows/ci.yml`): en cada push a `main` y en cada PR corre lint, tipos y tests de la API contra Postgres y RustFS, el build de la imagen de la API, y formato, lint, tipos y tests de la web. `make lint` y `make test` corren lo mismo en local.

## Comandos

| Comando | Qué hace |
|---|---|
| `make dev` | Levanta todo |
| `make seed` | Carga los datos de `config/seed.toml` |
| `make gen-client` | Regenera el cliente TypeScript después de cambiar la API |
| `make test` | Migra la base de tests y corre los tests |
| `make e2e` | Test de punta a punta contra `make dev` |
| `make lint` | Estilo y tipos de la API y la web |
| `make reset` | Borra los datos de Postgres y del almacenamiento |
| `make docker-api` | Construye la imagen de producción de la API |
| `make hooks` | Instala los hooks de git |
| `make help` | Lista todos los comandos |
