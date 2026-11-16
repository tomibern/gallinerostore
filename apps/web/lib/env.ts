import { parsePageSize } from "./listing";

// URL con la que el servidor de Next llega a la API (nunca la usa el navegador).
// Es una función para leer la variable recién cuando se necesita: next.config
// carga el .env de la raíz después de importar los módulos.
export function apiInternalUrl(): string {
  return process.env.API_INTERNAL_URL ?? "http://localhost:8000";
}

// Dónde están las fotos para el servidor de Next: Next reenvía /media/* acá
// (ADR 0003). Por defecto, el bucket del almacenamiento S3 local.
export function mediaInternalUrl(): string {
  const endpoint = process.env.S3_ENDPOINT_URL ?? "http://localhost:9000";
  const bucket = process.env.S3_BUCKET ?? "media";
  return process.env.MEDIA_INTERNAL_URL ?? `${endpoint}/${bucket}`;
}

// Productos por página del listado (20 por defecto). El e2e lo baja para tener
// varias páginas con pocos productos: LISTING_PAGE_SIZE=3 make dev.
export function listingPageSize(): number {
  return parsePageSize(process.env.LISTING_PAGE_SIZE);
}
