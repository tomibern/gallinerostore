# Skills del proyecto

Copiadas de [mattpocock/skills](https://github.com/mattpocock/skills) (MIT, commit `4ae2317`, 31/10/2026) en `.claude/skills/`, sin las carpetas `agents/` (solo sirven para Codex). Viajan con el repo, así que cada fork las hereda. Se pueden editar libremente.

## Flujo de trabajo

1. **Alinear**: `/grill-with-docs` (o `/grill-me`) sobre lo que se va a construir. Va dejando términos en `GLOSSARY.md` y decisiones en `docs/adr/`.
2. **Especificar**: `/to-spec` publica la spec como issue.
3. **Partir en tickets**: `/to-tickets` crea issues tracer-bullet con sus bloqueos.
4. **Construir**: `/implement` o `/implement-spec`, siempre con `/tdd`.
5. **Revisar**: `/code-review` (estándares del repo + lo que pedía el issue) y `/pr` para el cuerpo del PR.
6. **Cerrar**: `/retro` al terminar una sesión larga, `/handoff` para pasarla a otra.

Para trabajos que no entran en una sesión: `/wayfinder`. Para dudas sobre qué skill usar: `/ask-matt`.

## Actualizar

```bash
git clone --depth 1 https://github.com/mattpocock/skills /tmp/mp-skills
```

Comparar con `diff -r` contra `.claude/skills/` y traer lo que sirva, respetando lo que se haya adaptado acá. Actualizar el commit de arriba.
