# Desarrollar el núcleo en el repo de Gallinero y extraer el repo base después

El discovery prevé un repo base (template) del que cada cliente es un fork. Mientras haya un solo cliente, el núcleo se desarrolla directamente en `gallinerostore`, con todo lo específico de Gallinero aislado en `config/`, `brand/` y `custom/`. Cuando llegue el segundo cliente se extrae el repo base quitando esas carpetas y `gallinerostore` pasa a tener el base como `upstream`.

## Considered Options

- **Crear el repo base ahora y forkearlo desde el día 1**: descartado porque obliga a mantener dos repos y hacer un merge de upstream en cada cambio, con un solo desarrollador y sin segundo cliente que lo justifique.

## Consequences

La regla «en `apps/` no aparece nada del cliente» es lo que hace posible la extracción: se verifica en code review. Al extraer, el historial del base arranca de cero o se filtra con `git filter-repo`.
