// Cambiar la contraseña desde Cuenta: si el formulario está abierto, qué aviso se ve y
// qué error corresponde a cada respuesta de la API.
import type { ChangePasswordResult } from "./admin-api";
import { MIN_PASSWORD_LENGTH } from "./admin-paths";
import { t } from "./texts";

type PasswordFeedback = { kind: "error" | "done"; text: string } | null;

/** «Cambiar contraseña» en Cuenta: si el formulario está abierto y qué aviso se ve. */
export type PasswordChange = { open: boolean; feedback: PasswordFeedback };

export type PasswordChangeAction =
  { type: "open" } | { type: "cancel" } | { type: "saved" } | { type: "failed"; text: string };

export const PASSWORD_CHANGE_CLOSED: PasswordChange = { open: false, feedback: null };

/**
 * Abrir arranca sin avisos viejos; cancelar cierra sin aviso (lo escrito se borra al
 * desmontar el formulario); al guardar bien se cierra y queda la confirmación; con un
 * error sigue abierto para corregir.
 */
export function passwordChangeReducer(
  _state: PasswordChange,
  action: PasswordChangeAction,
): PasswordChange {
  switch (action.type) {
    case "open":
      return { open: true, feedback: null };
    case "cancel":
      return PASSWORD_CHANGE_CLOSED;
    case "saved":
      return { open: false, feedback: { kind: "done", text: t("admin.account.done") } };
    case "failed":
      return { open: true, feedback: { kind: "error", text: action.text } };
  }
}

export const TOO_SHORT = t("admin.password.tooShort", { min: MIN_PASSWORD_LENGTH });

/** El error a mostrar cuando la API no cambió la contraseña (sin sesión se va al login). */
export function passwordChangeError(
  result: Exclude<ChangePasswordResult, "ok" | "unauthorized">,
): string {
  if (result === "wrong_current") return t("admin.account.wrongCurrent");
  if (result === "too_short") return TOO_SHORT;
  return t("admin.login.error");
}
