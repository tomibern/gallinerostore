// Rutas del panel. Son del núcleo: no nombran nada del cliente.

export const ADMIN_HOME = "/admin/productos";
export const ADMIN_LOGIN = "/admin/login";

/**
 * A dónde volver después del login. Solo rutas del panel de este sitio: un `next` que
 * apunta a otro lado (otro dominio, `//evil`, la tienda) vuelve a la portada del panel.
 */
export function afterLoginPath(next: string | null | undefined): string {
  if (!next || !/^\/admin(\/|$)/.test(next) || next.startsWith(ADMIN_LOGIN)) return ADMIN_HOME;
  return next;
}
