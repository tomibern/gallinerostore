import { NextResponse, type NextRequest } from "next/server";

// Sin cookie de sesión, el panel lleva directo al login. Es solo una comodidad: la que
// valida la sesión es la API, y el panel vuelve al login si responde 401.
const SESSION_COOKIE = "admin_session";

export function proxy(request: NextRequest) {
  if (request.cookies.has(SESSION_COOKIE)) return NextResponse.next();
  const { pathname, search } = request.nextUrl;
  const login = new URL("/admin/login", request.url);
  login.searchParams.set("next", `${pathname}${search}`);
  return NextResponse.redirect(login);
}

export const config = {
  // Todo el panel salvo el login.
  matcher: ["/admin", "/admin/((?!login).*)"],
};
