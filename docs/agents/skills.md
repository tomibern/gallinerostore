# Skills del proyecto

Copiadas de [mattpocock/skills](https://github.com/mattpocock/skills) (MIT, commit `4ae2317`, 31/10/2026) en `.claude/skills/`, sin las carpetas `agents/` (solo sirven para Codex). Viajan con el repo, así que cada fork las hereda. Se pueden editar libremente.

Muchas son **de invocación manual** (`disable-model-invocation: true`): el agente no las ve ni las dispara solo; las corre la persona escribiendo `/grill-with-docs`, `/to-spec`, `/implement`, etc. Es a propósito: el humano decide cuándo grillar, especificar o implementar.

## Flujo de trabajo

El de Matt Pocock (ver `/ask-matt` y su `PHASE-BOUNDARIES.md`), aplicado a este proyecto. Una **funcionalidad** es lo que se piensa de una vez; en este proyecto, normalmente una fase del discovery.

### 1. Pensar: una vez por funcionalidad, en una sola sesión

Sin `/clear` ni `/compact` hasta terminar los tickets: el grill, la spec y los tickets salen del mismo razonamiento.

1. **`/research`** (opcional): si hace falta un dato externo (una API, el comportamiento del navegador de Instagram, una librería), un agente en segundo plano lo investiga en fuentes primarias y deja un archivo citado en `docs/research/`. Alimenta al grill; no lo reemplaza.
2. **`/grill-with-docs`**: entrevista hasta que no quede nada asumido. Deja términos en `GLOSSARY.md` y decisiones difíciles de revertir en `docs/adr/`.
3. **`/prototype`** (opcional): cuando una duda solo se resuelve viendo algo andando (una UI, una lógica de estados). El prototipo es descartable y queda en una rama `prototype/<nombre>`.
4. **`/to-spec`**: la spec como issue en GitHub.
5. **`/to-tickets`**: tickets tracer-bullet con sus bloqueos nativos, agrupados en épicas, en el tablero. **Cada ticket es el plan**: autocontenido, para que lo implemente alguien que no leyó la conversación.

### 2. Construir: un ticket por sesión, con contexto limpio

6. Por cada ticket libre de bloqueos, una **sesión nueva** con **`/implement #N`**. Esa misma sesión:
   - crea la rama `feat/<n>-<slug>` desde `main`;
   - construye con **`/tdd`** en las costuras acordadas en la spec;
   - cierra con **`/code-review`** (estándares y spec) y corrige lo que encuentre;
   - corre `make lint`, `make test` (y `make e2e` si toca la web), commitea por funcionalidad y abre la PR con **`/pr`** y `Closes #N`.
7. La persona revisa la PR y la mergea. Los tickets sin bloqueos entre sí pueden ir en sesiones paralelas.

Alternativa: **`/implement-spec`** construye todos los tickets de la spec con subagentes en paralelo sobre una rama de integración y una sola PR. Sirve cuando conviene orquestar en vez de ir ticket por ticket.

### 3. Cerrar: al terminar la funcionalidad

8. **`/retro`** en la sesión que se mira (antes de cerrarla): propone mejoras al **entorno**, no al código (chequeos automáticos, estándares, punteros en `CLAUDE.md`). Los errores mecánicos pasan a chequeos; los de criterio, a estándares.

### Por fuera del flujo

- **Bugs**: `/diagnosing-bugs` para los difíciles; después, `/retro`.
- **Issues que no creamos nosotros**: `/triage`. Los tickets de `/to-tickets` no se triagean.
- **Algo demasiado grande o difuso para una sesión**: `/wayfinder`, que termina en `/to-spec`.
- **Mantenimiento**: `/improve-codebase-architecture` cada tanto.
- **Pasar trabajo a otro agente, directorio o persona**: `/handoff`. No hace falta para implementar un ticket: el ticket ya es el plan.
- **¿Qué skill uso?**: `/ask-matt`.

## Actualizar

```bash
git clone --depth 1 https://github.com/mattpocock/skills /tmp/mp-skills
```

Comparar con `diff -r` contra `.claude/skills/` y traer lo que sirva, respetando lo que se haya adaptado acá. Actualizar el commit de arriba.
