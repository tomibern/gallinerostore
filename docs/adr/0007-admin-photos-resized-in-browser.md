# El panel achica las fotos en el navegador antes de subirlas

Las fotos del admin viajan por `/api/*`, que pasa por Next (ADR 0003). En producción (Netlify), ese reenvío corre dentro de la función del servidor de Next, con un límite fijo de 6 MB por pedido (unos 4,5 MB efectivos para binarios). En local, Next 16 corta en silencio todo lo que pase de 10 MB (`proxyClientMaxBodySize`), y FastAPI recibe un multipart roto. Una foto de un celular moderno pesa de 4 a 20 MB. Por eso el panel achica cada foto en el navegador, a unos 2048 px de lado mayor y JPEG de calidad 0,85, antes de subirla. La API sigue haciendo el procesamiento real: WebP de 1600 y de 400 px. No se guarda el original en alta resolución.

## Considered Options

- **Subir directo al bucket con una URL firmada**: evita todos los límites y conserva el original, pero suma un endpoint que firma la URL, un segundo paso en el que la API lee del bucket para procesar, y CORS en el bucket. No vale la pena mientras no haga falta el original.
- **Subir el original por `/api` y subir el límite de Next**: no alcanza, porque el límite de Netlify es fijo.

## Consequences

- Achicar la foto no es lógica de negocio: es preparar el envío. Los tamaños finales, el formato y las reglas (de 1 a 6 fotos, la portada) siguen en la API.
- Desde la galería, Safari en iOS entrega JPEG aunque la foto sea HEIC. Chrome en Android puede mandar HEIC y no lo sabe abrir para achicarlo. En ese caso el panel manda el archivo tal cual si pesa menos de 4 MB, y la API lo abre con `pillow-heif`. Si pesa más, el panel le pide al admin una captura o un JPEG.
- Si algún día hace falta el original (para imprimir, para un ecommerce con zoom), se pasa a la URL firmada sin cambiar el modelo: `product_images` ya guarda solo rutas.
