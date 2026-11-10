# El navegador habla solo con Next; la API y las fotos van detrás

El navegador nunca llama directo a la API ni al almacenamiento de fotos. Next reenvía `/api/*` a FastAPI y `/media/*` al almacenamiento compatible con S3 (MinIO en local; R2 o Supabase Storage en producción). Así la cookie httpOnly del admin es del mismo sitio (sin CORS ni `SameSite=None`), lo que importa sobre todo dentro del navegador de Instagram, y en desarrollo el celular funciona con una sola dirección (`http://<ip>:3000`). Esto reemplaza el subdominio público `api.gallinerostore.com.ar` que planteaba el discovery.

## Considered Options

- **API y fotos en orígenes propios** (`api.` y un dominio de CDN): descartado porque exige CORS y cookies entre sitios, que los navegadores embebidos bloquean o tratan de forma impredecible.

## Consequences

Todo el tráfico del navegador a la API pasa por Next (Netlify en producción), que suma un salto. Las fotos se pueden servir directo desde el dominio público del bucket si el reenvío resulta lento, porque son públicas y no necesitan cookie.
