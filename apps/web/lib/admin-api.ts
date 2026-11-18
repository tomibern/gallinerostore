// Acceso a la API del admin desde el navegador. Como el resto, pasa por /api/* (ADR
// 0003), así la cookie de sesión es del mismo sitio. Todas las llamadas llevan el header
// anti-CSRF que exigen las escrituras del admin. Sin imports del servidor.

import {
  createApiClient,
  type AdminOut,
  type AdminSettings,
  type AdminSettingsIn,
  type LoginIn,
  type MessageCase,
  type MessagePreview,
  type ValidationError,
} from "@catalog/api-client";

import { fieldErrors, type FieldErrors } from "./admin-settings";

export type { AdminOut, AdminSettings, AdminSettingsIn, MessageCase, MessagePreview };

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

/** Contacto, mensajes prearmados y aviso de encargue. Sin sesión, null. */
export async function getAdminSettings(): Promise<AdminSettings | null> {
  const { data, response } = await api.GET("/admin/settings", { cache: "no-store" });
  if (data) return data;
  if (response.status === 401) return null;
  throw new Error(`GET /admin/settings respondió ${response.status}`);
}

export type ApiResult<T> =
  { status: "ok"; data: T } | { status: "invalid"; errors: FieldErrors } | { status: "error" };

async function withFieldErrors<T>(
  request: Promise<{ data?: T; error?: unknown; response: Response }>,
): Promise<ApiResult<T>> {
  try {
    const { data, error, response } = await request;
    if (data) return { status: "ok", data };
    if (response.status === 422) {
      const detail = (error as { detail?: ValidationError[] } | undefined)?.detail ?? [];
      return { status: "invalid", errors: fieldErrors(detail) };
    }
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
