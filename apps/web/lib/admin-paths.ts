// Rutas del panel. Son del núcleo: no nombran nada del cliente.

export const ADMIN_HOME = "/admin/productos";
export const ADMIN_LOGIN = "/admin/login";
// Las pantallas de contraseña sin sesión. La API arma los links de los emails con estas
// mismas rutas.
export const ADMIN_FORGOT_PASSWORD = "/admin/recuperar";
export const ADMIN_CHOOSE_PASSWORD = "/admin/elegir-contrasena";
export const ADMIN_PUBLIC_PATHS = [ADMIN_LOGIN, ADMIN_FORGOT_PASSWORD, ADMIN_CHOOSE_PASSWORD];

/** Mínimo de la contraseña nueva. La API lo exige; la web lo usa para avisar antes. */
export const MIN_PASSWORD_LENGTH = 10;

/** Qué le falta a la contraseña nueva antes de mandarla, o null si está bien. */
export function newPasswordProblem(password: string, repeat: string): "short" | "mismatch" | null {
  if (password.length < MIN_PASSWORD_LENGTH) return "short";
  if (password !== repeat) return "mismatch";
  return null;
}

/**
 * A dónde volver después del login. Solo rutas del panel de este sitio: un `next` que
 * apunta a otro lado (otro dominio, `//evil`, la tienda) vuelve a la portada del panel.
 */
export function afterLoginPath(next: string | null | undefined): string {
  if (
    !next ||
    !/^\/admin(\/|$)/.test(next) ||
    ADMIN_PUBLIC_PATHS.some((path) => next.startsWith(path))
  ) {
    return ADMIN_HOME;
  }
  return next;
}
