// URL con la que el servidor de Next llega a la API (nunca la usa el navegador).
// Es una función para leer la variable recién cuando se necesita: next.config
// carga el .env de la raíz después de importar los módulos.
export function apiInternalUrl(): string {
  return process.env.API_INTERNAL_URL ?? "http://localhost:8000";
}
