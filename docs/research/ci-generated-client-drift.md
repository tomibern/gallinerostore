# La CI verifica que el cliente generado esté al día (issue #10)

Investigación para el ticket #10: un job de CI que regenera `packages/api-client` desde el OpenAPI actual de la API y falla si difiere de lo commiteado. Fecha: 2026-11-11.

## Recomendaciones (resumen)

1. **El check es `make gen-client` + git.** Agregar `make check-client` (o similar) que corra `gen-client` y después `git status --porcelain -- packages/api-client`; si hay salida, imprime `::error::` (en CI), el `git diff` y "corré `make gen-client` y commiteá el resultado", y sale con 1. No usar solo `git diff --exit-code`: no ve archivos nuevos sin trackear.
2. **Cubrir los dos artefactos**: `packages/api-client/openapi.json` y `packages/api-client/src/schema.d.ts`. Si cambia el esquema, cambian los dos. Un drift en `openapi.json` sin cambio en `.d.ts` (por ejemplo, una `description`) también es drift real del contrato commiteado.
3. **No usar `openapi-typescript --check` como mecanismo principal.** Solo compara `schema.d.ts` contra `openapi.json`, que es un archivo commiteado. No detecta que la API cambió si nadie regeneró `openapi.json`.
4. **Hoy la salida ya es determinista y reproducible**: la regeneré localmente y es byte a byte igual a lo commiteado (ver "Estado actual"). La reproducibilidad depende de los lockfiles (`uv.lock`, `package-lock.json`). Por eso la CI tiene que usar `uv sync --frozen` y `npm ci`.
5. **Hay que destrabar dos cosas para la CI.** (a) El `Makefile` corta si no existe `.env` (`Makefile:8-13`): agregar el target del check y `gen-client` a `ENV_FREE_GOALS`, o hacer `cp .env.example .env` en el job. (b) `Settings()` exige `DATABASE_URL`, `S3_ENDPOINT_URL`, `S3_ACCESS_KEY` y `S3_SECRET_KEY` aunque exportar el OpenAPI no se conecte a nada. Alcanzan valores dummy en el `env:` del job. No hacen falta los `services` de Postgres ni de RustFS.
6. **Job nuevo `api-client`** en `.github/workflows/ci.yml`, con `actions/checkout@v7`, `astral-sh/setup-uv@v10.3.3` (no existe tag `v10`), `actions/setup-node@v7` con `node-version-file: .nvmrc` y `cache: npm`, y después `uv sync --frozen` (en `apps/api`), `npm ci` y `make check-client`. Mismas versiones que los jobs actuales.
7. **Opcional:** agregar un `.gitattributes` con `* text=auto eol=lf` (o al menos `packages/api-client/** text eol=lf`). Así un dev en Windows con `core.autocrlf` no genera un drift falso, o uno real que se oculta. Para la CI en Ubuntu no hace falta.

## Estado actual del repo

- `make gen-client` (`Makefile:42-44`):
  1. `cd apps/api && uv run python -m app.cli openapi > ../../packages/api-client/openapi.json`
  2. `npm run generate -w @catalog/api-client`
- `app.cli openapi` (`apps/api/app/cli.py:57-58`) hace `print(json.dumps(create_app(settings).openapi(), indent=2, ensure_ascii=False))`. No usa `sort_keys`, y `print` agrega un `\n` final. Antes construye `Settings()` (`cli.py:51`).
- `Settings` (`apps/api/app/core/config.py:52-64`): `database_url`, `s3_endpoint_url`, `s3_access_key` y `s3_secret_key` no tienen default, así que son obligatorias. Lee `.env` de la raíz si existe (`config.py:53`).
- `create_app` (`apps/api/app/main.py:17-35`) solo abre la base y crea el cliente S3 dentro del `lifespan`. `.openapi()` no dispara el lifespan, así que exportar no se conecta a nada. Los routers usan `StoreConfig` solo como dependencia en runtime (`modules/catalog/router.py:19`, `modules/settings/router.py:13`), así que el OpenAPI no depende de `config/store.toml`. El título es genérico ("Catalog API", `main.py:30-31`).
- Generador: `openapi-typescript` (`packages/api-client/package.json:10-14`), con script `openapi-typescript openapi.json --output src/schema.d.ts` y rango `^7.13.0`. El lockfile fija **7.13.0** (`package-lock.json:6108-6111`) y TypeScript **5.9.3** (`package-lock.json:7382-7383`). No hay `redocly.yaml`, así que usa la config `minimal` por defecto (`node_modules/openapi-typescript/bin/cli.js:221-222`).
- Los dos archivos están commiteados (`git ls-files packages/api-client`: `openapi.json`, `package.json`, `src/index.ts`, `src/schema.d.ts`). Ninguno está en `.gitignore`.
- Prettier **ignora** los dos generados (`.prettierignore`: `packages/api-client/openapi.json` y `packages/api-client/src/schema.d.ts`). El hook `prettier` de pre-commit (`.pre-commit-config.yaml`, `npx prettier --write --ignore-unknown`) respeta `.prettierignore`, así que no los reescribe. Tampoco `npm run format:check` en CI. No hay `.gitattributes`.
- CI actual (`.github/workflows/ci.yml`): jobs `api` (`:18-69`, con `setup-uv@v10.3.3`, uv `0.11.7` y `uv sync --frozen`), `api-image` y `web` (`:79-96`, con `setup-node@v7`, `.nvmrc` = `22`, `cache: npm` y `npm ci`). No hay ningún check del cliente.
- Versiones del lado Python: Python `3.13` (`apps/api/.python-version`), FastAPI **0.162.4** y Pydantic **2.14.3** (`apps/api/uv.lock:305-306`, `:880-881`).
- **Prueba de reproducibilidad (local, Node v22.21.1, Linux):** con solo las 4 variables dummy en el entorno, `uv run --frozen python -m app.cli openapi` produjo un `openapi.json` idéntico (`cmp`) al commiteado. `openapi-typescript openapi.json` produjo un `schema.d.ts` idéntico al commiteado.
- `docs/discovery.md:363` dice "openapi-typescript u Orval". Se eligió openapi-typescript (commit `9076c4d`).

## 1. ¿La salida del generador es determinista?

- **Encabezado sin versión ni fecha.** El header es fijo: "This file was auto-generated by openapi-typescript. Do not make direct changes to the file." (`node_modules/openapi-typescript/dist/index.mjs:21-24`). Subir de versión no cambia el header, aunque sí puede cambiar el cuerpo.
- **Fin de línea fijo en LF.** Imprime con el printer de TypeScript usando `newLine: ts.NewLineKind.LineFeed` (`dist/lib/ts.mjs:163-164`). No depende del SO.
- **Orden.** Por defecto respeta el orden del documento de entrada. Con `--alphabetize` ordena con `localeCompare(..., "en-us", { numeric: true })` (`dist/lib/utils.mjs:85-86`). No hace falta, porque el orden de entrada ya es determinista (ver punto 2). Además, `localeCompare` depende de ICU, lo que es una fuente teórica de variación entre builds de Node. Fuente del flag: https://openapi-ts.dev/cli
- **No usa formatter.** No invoca Prettier: el formato lo da el printer de TS. Por eso la salida depende de la versión exacta de `openapi-typescript` y de `typescript`, que fija `package-lock.json`.
- **Cómo fijarlo:** `npm ci` en CI, que instala exactamente lo del lockfile. Opcionalmente, pasar `"openapi-typescript": "7.13.0"` sin `^` para que un `npm install` local no lo suba sin querer. Un bump de versión se commitea junto con la regeneración, igual que con cualquier lockfile (regla de `CLAUDE.md`).
- **No verificado:** no probé otras versiones de Node (24) ni macOS/Windows. Por el código (LF fijo, sin timestamps, sin orden dependiente de locale si no se usa `--alphabetize`) no se espera variación.
- **`--check`:** existe ("Check that the generated types are up-to-date.", https://openapi-ts.dev/cli). Implementación: lee el archivo de salida, compara con `===` y sale con 1 y "Generated types are not up-to-date!" (`bin/cli.js:125-135`). Lo agregó el PR #1768 (CHANGELOG). Solo cubre `.d.ts` contra el `openapi.json` commiteado, así que no alcanza para este ticket (recomendación 3).

## 2. ¿`app.openapi()` es determinista? ¿Requiere base o variables?

- **Orden de claves:** los dicts de Python preservan el orden de inserción (garantía del lenguaje desde 3.7). FastAPI arma los `paths` en el orden en que se registran las rutas (`main.py:32-34`). Además ordena explícitamente los esquemas: `components["schemas"] = {k: definitions[k] for k in sorted(definitions)}` (`apps/api/.venv/.../fastapi/openapi/utils.py:661`, FastAPI 0.162.4). Pydantic ordena las claves de los JSON Schema que genera (`GenerateJsonSchema.sort`, `.venv/.../pydantic/json_schema.py:593-613`).
- **Serialización:** `json.dumps` usa `sort_keys=False` por defecto. Con `indent` distinto de `None`, los separadores por defecto son `(',', ': ')`, sin espacios al final de línea. `ensure_ascii=False` deja los caracteres no ASCII tal cual. `dumps` no agrega newline final; lo agrega `print`. Fuente: https://docs.python.org/3/library/json.html#json.dumps. Esto es estable entre plataformas. Agregar `sort_keys=True` no hace falta y además cambiaría el orden de `paths` respecto de lo commiteado, lo que generaría un diff de una sola vez.
- **Cache:** `FastAPI.openapi()` cachea en `app.openapi_schema` y lo recalcula si cambia la versión de rutas (`.venv/.../fastapi/applications.py`, método `openapi`). No hay efecto de estado entre corridas porque cada CLI crea una app nueva.
- **Variables y base:** no se conecta a la base ni a S3, pero `Settings()` falla si faltan las 4 variables obligatorias (`config.py:55-58`). Comprobado: funciona con `DATABASE_URL=x S3_ENDPOINT_URL=x S3_ACCESS_KEY=x S3_SECRET_KEY=x`. El `Makefile` además exige `.env` para cualquier target fuera de `help reset hooks` (`Makefile:8-13`).
- **Riesgo a futuro:** si alguna vez el OpenAPI pasa a depender de `store.toml` (por ejemplo, rutas condicionadas por `features`), la salida va a depender de la configuración del cliente. Eso choca con "Núcleo genérico", y conviene que el check lo detecte, porque el diff aparecería en un fork.

## 3. Detectar el drift: `git diff --exit-code` contra `git status --porcelain`

- `git diff --exit-code`: "exits with 1 if there were differences and 0 means no differences". `--quiet` implica `--exit-code` (https://git-scm.com/docs/git-diff). Sin argumentos compara el working tree contra el index, así que **no ve archivos sin trackear**. Si el generador crea un archivo nuevo, pasa en verde. La doc no lo dice explícitamente con estas palabras: se deduce de la definición (working tree contra index).
- `git status --porcelain` (v1): formato "guaranteed not to change in a backwards-incompatible way between Git versions or based on user configuration". Los no trackeados salen como `??`, y por defecto se muestran (`--untracked-files=normal`) (https://git-scm.com/docs/git-status). Muestra modificados, borrados (` D`) y nuevos. **No cambia el exit code** según haya cambios o no (la doc no documenta exit codes), así que hay que testear si la salida está vacía.
- Receta propuesta (bash, dentro del target de make):

  ```bash
  make gen-client
  if [ -n "$(git status --porcelain -- packages/api-client)" ]; then
    msg="El cliente generado no está al día con el OpenAPI de la API. Corré \`make gen-client\` y commiteá el resultado."
    [ -n "$GITHUB_ACTIONS" ] && echo "::error title=Cliente desactualizado::$msg"
    echo "$msg" >&2
    git status --porcelain -- packages/api-client
    git --no-pager diff -- packages/api-client
    exit 1
  fi
  ```

  Limitar la ruta a `packages/api-client` evita falsos positivos por otros archivos que se toquen en el job. Aun así, `git status` en CI debería estar limpio después de `npm ci` y `uv sync`, porque `node_modules/` y `.venv/` están en `.gitignore`.
- **Mensaje en Actions:** la sintaxis es `::error file={name},line={line},endLine={endLine},title={title}::{message}`, y crea una anotación además de imprimir la línea en el log (https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands). Para que aparezca en la vista de la run, se puede agregar al resumen con `echo "..." >> "$GITHUB_STEP_SUMMARY"`. Acepta GitHub-flavored Markdown, con un límite de 1 MiB por paso (misma página). Una opción es un bloque ```` ```diff ```` con el diff, truncado si es grande.
- **Localmente:** en local no existe `GITHUB_ACTIONS`, así que solo se imprime el mensaje y el diff. Ojo: localmente el check **modifica** los archivos (regenera). Si el dev tenía cambios sin commitear en `packages/api-client`, el check falla por eso. Es aceptable y conviene decirlo en el `## help` del target.

## 4. Toolchain en Actions

- **Node:** `actions/setup-node@v7` es la mayor actual (README: `uses: actions/setup-node@v7`; último release v7.1.0 según `gh api`). Con `node-version-file: .nvmrc` y `cache: npm` cachea según `package-lock.json` de la raíz, no `node_modules` (https://github.com/actions/setup-node). Igual que el job `web` (`ci.yml:84-88`). El caché automático de npm sin input `cache` solo se activa si `package.json` tiene `packageManager`, y este repo no lo tiene, así que hay que poner `cache: npm` explícito.
- **Python/uv:** `astral-sh/setup-uv`. Último release v10.3.3. **No existe el tag `v10`** (`gh api repos/astral-sh/setup-uv/git/ref/tags/v10` devuelve 404, aunque sí existe `v7`), coherente con el comentario de `ci.yml:54`. Inputs relevantes: `version`, `enable-cache` (default `auto`), `working-directory` (donde busca `pyproject.toml`, `uv.lock` y `.python-version`) y `cache-dependency-glob` (por defecto incluye `uv.lock`) (https://github.com/astral-sh/setup-uv). Usar `version: "0.11.7"` y `uv sync --frozen` como el job `api`. Python 3.13 sale de `apps/api/.python-version`; uv lo descarga si hace falta.
- **Esqueleto del job** (sin services):

  ```yaml
  api-client:
    name: Cliente de la API (al día con el OpenAPI)
    runs-on: ubuntu-latest
    env:
      DATABASE_URL: postgresql+asyncpg://unused@localhost/unused
      S3_ENDPOINT_URL: http://localhost:9000
      S3_ACCESS_KEY: unused
      S3_SECRET_KEY: unused
    steps:
      - uses: actions/checkout@v7
      - uses: astral-sh/setup-uv@v10.3.3
        with: { version: "0.11.7", enable-cache: true, working-directory: apps/api }
      - uses: actions/setup-node@v7
        with: { node-version-file: .nvmrc, cache: npm }
      - run: uv sync --frozen
        working-directory: apps/api
      - run: npm ci
      - run: make check-client
  ```

  Ojo con `make` y `.env`: con `-include .env` + `export` (`Makefile:5-6`), si existiera un `.env` sus valores pisarían los del `env:` del job. En CI no hay `.env`, así que esto solo importa si se elige la alternativa `cp .env.example .env`. **No verificado:** si `.env.example` trae las 4 variables, porque no lo leí.

## 5. Alcance del check y trampas

- **Cubrir `openapi.json` y `src/`.** `openapi.json` es el insumo intermedio commiteado. Si solo se mirara `schema.d.ts`, un cambio de esquema que no afecte los tipos (descripciones, `operationId`) dejaría el `openapi.json` commiteado viejo. `src/index.ts` es escrito a mano y el generador no lo toca, así que no aparece en el diff. Incluir todo `packages/api-client` en el `git status` es simple y correcto.
- **`.gitignore`:** ninguno de los generados está ignorado (bien). Si alguno lo estuviera, `git status` no lo vería y el check sería ciego.
- **Formatter:** prettier ya los excluye (`.prettierignore`). Si alguien los saca de ahí, el hook de pre-commit los reformatearía y la CI marcaría drift permanente. Conviene dejar un comentario en `.prettierignore` que lo explique. `ruff` no toca nada fuera de `apps/api`.
- **Fin de línea:** sin `.gitattributes`, en Windows con `core.autocrlf=true` el checkout trae CRLF y el generador escribe LF, lo que da diffs espurios en local (en el index se normaliza, pero `git status` puede marcarlos). Con `* text=auto eol=lf`, los archivos de texto se normalizan a LF en el index y se escriben con LF en el working tree (https://git-scm.com/docs/gitattributes). Opcional: hoy el equipo trabaja en Linux.
- **Bump del generador:** subir `openapi-typescript` (o `typescript`) puede cambiar el `.d.ts` sin cambiar la API. El check va a fallar en esa PR hasta regenerar. Es el comportamiento deseado.

## 6. Cómo lo hacen otros

- El propio `openapi-typescript` trae `--check` para este caso de uso ("Check that the generated types are up-to-date", https://openapi-ts.dev/cli). Confirma el patrón regenerar y comparar, pero como vimos solo cubre el segundo paso.
- No busqué ni verifiqué otros proyectos de referencia. El patrón genérico regenerar + `git status --porcelain`/`git diff --exit-code` es común, pero acá no lo respaldo con una fuente primaria concreta.
