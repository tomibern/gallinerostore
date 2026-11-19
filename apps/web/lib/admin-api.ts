// Acceso a la API del admin desde el navegador. Como el resto, pasa por /api/* (ADR
// 0003), así la cookie de sesión es del mismo sitio. Todas las llamadas llevan el header
// anti-CSRF que exigen las escrituras del admin. Sin imports del servidor.

import {
  createApiClient,
  type AdminFilter,
  type AdminOut,
  type AdminProduct,
  type AdminProductCreate,
  type AdminProductPatch,
  type AdminProductList,
  type AdminProductListItem,
  type AdminSettings,
  type AdminSettingsIn,
  type CatalogOptions,
  type LoginIn,
  type MessageCase,
  type MessagePreview,
  type MetricsPeriod,
  type MetricsSummary,
  type ValidationError,
  type PasswordChangeIn,
  type PasswordResetConfirmIn,
  type SaleMode,
} from "@catalog/api-client";

import { productFieldErrors } from "./admin-product";
import { fieldErrors, type FieldErrors } from "./admin-settings";

export type {
  AdminFilter,
  AdminOut,
  AdminProduct,
  AdminProductCreate,
  AdminProductPatch,
  AdminProductList,
  AdminProductListItem,
  AdminSettings,
  AdminSettingsIn,
  CatalogOptions,
  MessageCase,
  MessagePreview,
  MetricsPeriod,
  MetricsSummary,
  SaleMode,
};

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

/** Contacto, mensajes prearmados y aviso de encargue. Sin sesión, null. */
export async function getAdminSettings(): Promise<AdminSettings | null> {
  const { data, response } = await api.GET("/admin/settings", { cache: "no-store" });
  if (data) return data;
  if (response.status === 401) return null;
  throw new Error(`GET /admin/settings respondió ${response.status}`);
}

export type ApiResult<T> =
  | { status: "ok"; data: T }
  | { status: "invalid"; errors: FieldErrors }
  | { status: "unauthorized" }
  | { status: "error" };

async function withFieldErrors<T>(
  request: Promise<{ data?: T; error?: unknown; response: Response }>,
  toFieldErrors: (detail: ValidationError[]) => FieldErrors = fieldErrors,
): Promise<ApiResult<T>> {
  try {
    const { data, error, response } = await request;
    if (data) return { status: "ok", data };
    if (response.status === 422) {
      const detail = (error as { detail?: ValidationError[] } | undefined)?.detail ?? [];
      return { status: "invalid", errors: toFieldErrors(detail) };
    }
    if (response.status === 401) return { status: "unauthorized" };
    return { status: "error" };
  } catch {
    return { status: "error" };
  }
}

/** Guarda contacto, plantillas y aviso. Si algo no vale, los errores por campo. */
export function saveAdminSettings(body: AdminSettingsIn): Promise<ApiResult<AdminSettings>> {
  return withFieldErrors(api.PUT("/admin/settings", { body }));
}

/** El mensaje que armaría la API con esa plantilla, con un producto publicado real. */
export function previewMessage(
  messageCase: MessageCase,
  template: string,
): Promise<ApiResult<MessagePreview>> {
  return withFieldErrors(
    api.POST("/admin/settings/message-preview", { body: { case: messageCase, template } }),
  );
}

/** «Olvidé mi contraseña». La API siempre acepta: no dice si el email existe. */
export async function requestPasswordReset(email: string): Promise<"ok" | "error"> {
  try {
    const { response } = await api.POST("/admin/password-reset", { body: { email } });
    return response.ok ? "ok" : "error";
  } catch {
    return "error";
  }
}

export type ChoosePasswordResult = "ok" | "invalid" | "too_short" | "error";

/** Elige la contraseña desde el link del email. Si sale bien, ya hay sesión. */
export async function confirmPasswordReset(
  body: PasswordResetConfirmIn,
): Promise<ChoosePasswordResult> {
  try {
    const { response } = await api.POST("/admin/password-reset/confirm", { body });
    if (response.ok) return "ok";
    if (response.status === 400) return "invalid";
    if (response.status === 422) return "too_short";
    return "error";
  } catch {
    return "error";
  }
}

export type ChangePasswordResult = "ok" | "wrong_current" | "too_short" | "unauthorized" | "error";

/** Cambia la contraseña desde Cuenta, con la actual. */
export async function changePassword(body: PasswordChangeIn): Promise<ChangePasswordResult> {
  try {
    const { response } = await api.PUT("/admin/password", { body });
    if (response.ok) return "ok";
    if (response.status === 400) return "wrong_current";
    if (response.status === 422) return "too_short";
    if (response.status === 401) return "unauthorized";
    return "error";
  } catch {
    return "error";
  }
}

/** Una página del listado del admin, o null si la sesión ya no vale (401). */
export async function getAdminProducts(query: {
  q: string;
  filter: AdminFilter;
  offset: number;
  limit: number;
}): Promise<AdminProductList | null> {
  const { data, response } = await api.GET("/admin/products", {
    params: { query: { ...query, q: query.q || undefined } },
    cache: "no-store",
  });
  if (data) return data;
  if (response.status === 401) return null;
  throw new Error(`GET /admin/products respondió ${response.status}`);
}

/** Lo que el editor ofrece para elegir, o null si la sesión ya no vale (401). */
export async function getCatalogOptions(): Promise<CatalogOptions | null> {
  const { data, response } = await api.GET("/admin/catalog-options", { cache: "no-store" });
  if (data) return data;
  if (response.status === 401) return null;
  throw new Error(`GET /admin/catalog-options respondió ${response.status}`);
}

/** Un producto para editarlo: "not_found" si no existe, null si la sesión ya no vale. */
export async function getAdminProduct(code: string): Promise<AdminProduct | "not_found" | null> {
  const { data, response } = await api.GET("/admin/products/{code}", {
    params: { path: { code } },
    cache: "no-store",
  });
  if (data) return data;
  if (response.status === 401) return null;
  if (response.status === 404) return "not_found";
  throw new Error(`GET /admin/products/${code} respondió ${response.status}`);
}

/** Crea un borrador; la API le asigna el código. Si algo no vale, los errores por campo. */
export function createAdminProduct(body: AdminProductCreate): Promise<ApiResult<AdminProduct>> {
  return withFieldErrors(api.POST("/admin/products", { body }), productFieldErrors);
}

/** Guarda los cambios de un producto. Si algo no vale, los errores por campo. */
export function updateAdminProduct(
  code: string,
  body: AdminProductPatch,
): Promise<ApiResult<AdminProduct>> {
  return withFieldErrors(
    api.PATCH("/admin/products/{code}", { params: { path: { code } }, body }),
    productFieldErrors,
  );
}
