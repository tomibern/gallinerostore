# RustFS como almacenamiento de fotos en local

El discovery planteaba MinIO en Docker para las fotos en desarrollo. MinIO dejó de publicar imágenes en Docker Hub, así que en local usamos RustFS (`rustfs/rustfs`, con versión fija en `docker-compose.yml`), que habla la misma API S3. La API solo conoce un almacenamiento compatible con S3 (endpoint, bucket y credenciales por variables de entorno), así que cambiar de proveedor no toca código: en producción sigue la idea de Cloudflare R2 o Supabase Storage.

## Considered Options

- **MinIO desde el código fuente o con imágenes de terceros**: descartado porque habría que compilarlo o confiar en imágenes sin mantenimiento oficial.

## Consequences

La documentación nombra el almacenamiento de forma genérica («compatible con S3») y no un producto. Si RustFS deja de servir, se cambia la imagen en `docker-compose.yml` y las variables `S3_*`, sin migraciones ni cambios en la API.
