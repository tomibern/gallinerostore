# La API entrega los mensajes prearmados ya armados en el detalle del producto

El mensaje prearmado es lógica de negocio: plantillas de `settings.message_templates`, casos de disponibilidad, talle y código. Por eso lo arma la API. Pero el clic de «Consultar» tiene que abrir WhatsApp o copiar al portapapeles de forma sincrónica, dentro del gesto del usuario: si antes hay un `await`, el navegador de Instagram puede bloquear el portapapeles o la apertura del link. Por eso el detalle del producto trae, para cada talle y cada canal, el mensaje y el link ya armados, y la web solo elige cuál usar. La consulta se registra aparte, con `sendBeacon` a `POST /events`, sin esperar la respuesta.

## Considered Options

- **Pedir el mensaje a la API al hacer clic**: una sola fuente de lógica y respuestas más chicas, pero el `await` rompe el gesto del usuario en los navegadores embebidos.
- **Replicar las plantillas en TypeScript**: el clic es sincrónico, pero la lógica queda duplicada en la web, contra la regla de que la web no tiene lógica de negocio.

## Consequences

La respuesta del detalle crece con talles × canales (con 6 talles y 2 canales, 12 mensajes: consultar exige elegir talle). Si se suma un canal o un talle, el detalle trae más mensajes sin cambios en la web.
