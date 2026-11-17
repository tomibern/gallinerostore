# Las sesiones del admin se guardan en Postgres, no en un JWT

El admin entra con email y contraseña y recibe una cookie httpOnly con un id de sesión opaco, del mismo sitio gracias a ADR 0003. La sesión vive en una tabla de Postgres. Así se puede revocar: cerrar sesión, cambiar la contraseña o recuperarla por email corta todas las sesiones abiertas al instante. Eso importa porque el dueño entra desde su celular y puede perderlo. La sesión común dura hasta cerrar el navegador. Con «Mantener la sesión iniciada» dura 30 días y se renueva con el uso.

## Considered Options

- **JWT firmado en la cookie**: no consulta la base en cada pedido, pero no se puede revocar antes de que venza sin agregar una lista de revocados, que es otra tabla. Con un solo usuario y poco tráfico, la consulta extra no pesa.

## Consequences

- La API también usa la sesión para descartar los eventos del admin cuando navega su propia tienda: el `sendBeacon` lleva la cookie porque es del mismo sitio.
- Las sesiones vencidas se borran solas al validar o con una limpieza periódica. No hace falta un job aparte mientras la tabla sea chica.
