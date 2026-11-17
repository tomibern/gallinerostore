# La IP del límite de frecuencia sale de la derecha de `X-Forwarded-For`

El límite de frecuencia de `POST /events` cuenta por IP, pero la API nunca ve al visitante: todo pasa por Next (ADR 0003). La IP llega en `X-Forwarded-For`, y lo de la izquierda de ese header lo escribe quien quiera: Next lo copia tal cual al reenviar `/api/*` y no le agrega nada. Por eso la API toma la entrada que agregó el último proxy de confianza, contando desde la derecha: `Settings.trusted_proxy_hops` (1 por defecto). Si esa entrada falta o no es una IP, cuenta la dirección de la conexión. Una IPv6 cuenta con todo su `/64`. La IP solo es la clave de un contador en memoria: no se guarda.

## Considered Options

- **El primer valor de `X-Forwarded-For`**: es el que recomiendan muchas guías, pero lo elige el cliente; cambiándolo, cada pedido tendría cupo nuevo.
- **`get_ipaddr` de slowapi**: busca el header `X_FORWARDED_FOR` (con guiones bajos, no coincide con el estándar) y devuelve la lista entera.
- **El `ProxyHeadersMiddleware` de uvicorn** (`--forwarded-allow-ips`): confía en los proxies por dirección, pero en producción la dirección de Next depende del hosting y no se conoce de antemano.

## Consequences

- Cuántos proxies agregan entradas delante de Next en producción (Netlify) no está verificado: se ajusta `TRUSTED_PROXY_HOPS` en la Fase 5. Con un valor de más, el límite se puede eludir; con uno de menos, todos comparten el balde del proxy.
- En desarrollo nadie agrega el header: cuenta la conexión, que es la de Next, así que el límite es uno para todos. El e2e lo apaga con `RATE_LIMIT_ENABLED=false`.
- El límite es generoso (120 por minuto) porque muchos celulares pueden salir por la misma IP pública.
- Los contadores viven en el proceso: con varios workers, cada uno cuenta por su lado.
