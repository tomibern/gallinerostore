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
| `packages/` | Paquetes compartidos (el cliente generado de la API llega en #7). |
| `config/store.toml` | Datos de la tienda del cliente: nombre, moneda, prefijo de código, features. |
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
git config core.hooksPath .githooks
```

```bash
cp .env.example .env
```

```bash
make dev
```

`make dev` instala dependencias, levanta Postgres y el almacenamiento, espera a que estén sanos, aplica las migraciones y arranca la API y la web con recarga automática. `Ctrl+C` corta todo.

- Web: <http://localhost:3000>
- Desde el celular (misma wifi): `http://<ip-de-la-compu>:3000` (`make dev` la imprime al arrancar)
- API directa: <http://localhost:8000/docs>
- Consola del almacenamiento: <http://localhost:9001>

Postgres se publica en el puerto 5433 para no chocar con un Postgres instalado en la máquina.

## Comandos

| Comando | Qué hace |
|---|---|
| `make dev` | Levanta todo |
| `make test` | Migra la base de tests y corre los tests |
| `make lint` | Estilo y tipos de la API y la web |
| `make reset` | Borra los datos de Postgres y del almacenamiento |
| `make docker-api` | Construye la imagen de producción de la API |
| `make help` | Lista todos los comandos |
