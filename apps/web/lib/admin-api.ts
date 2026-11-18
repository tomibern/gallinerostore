// Acceso a la API del admin desde el navegador. Como el resto, pasa por /api/* (ADR
// 0003), así la cookie de sesión es del mismo sitio. Todas las llamadas llevan el header
// anti-CSRF que exigen las escrituras del admin. Sin imports del servidor.

import {
  createApiClient,
  type AdminOut,
  type LoginIn,
  type MetricsPeriod,
  type MetricsSummary,
} from "@catalog/api-client";

export type { AdminOut, MetricsPeriod, MetricsSummary };

export const CSRF_HEADERS = { "X-Requested-With": "fetch" };

const api = createApiClient("/api", CSRF_HEADERS);

/** El admin de la sesión actual, o null si no hay sesión vigente. */
export async function getAdminSession(): Promise<AdminOut | null> {
  const { data, response } = await api.GET("/admin/session", { cache: "no-store" });
  if (data) return data;
  if (response.status === 401) return null;
  throw new Error(`GET /admin/session respondió ${response.status}`);
}

export type LoginResult = "ok" | "invalid" | "too_many" | "error";

/** Abre una sesión. No distingue email de contraseña incorrectos: la API tampoco. */
export async function logIn(body: LoginIn): Promise<LoginResult> {
  try {
    const { response } = await api.POST("/admin/session", { body });
    if (response.ok) return "ok";
    if (response.status === 401) return "invalid";
    if (response.status === 429) return "too_many";
    return "error";
  } catch {
    return "error";
  }
}

/** Cierra la sesión (y borra la cookie). */
export async function logOut(): Promise<void> {
  await api.DELETE("/admin/session");
}

/** El resumen de métricas del período, o null si la sesión ya no está vigente. */
export async function getMetricsSummary(period: MetricsPeriod): Promise<MetricsSummary | null> {
  const { data, response } = await api.GET("/admin/metrics/summary", {
    params: { query: { period } },
    cache: "no-store",
  });
  if (data) return data;
  if (response.status === 401) return null;
  throw new Error(`GET /admin/metrics/summary respondió ${response.status}`);
}
