// Errores de la API de ajustes del admin, llevados a cada campo del formulario. La
// validación es de la API; acá solo se elige el texto del diccionario para mostrarla.

import type { ValidationError } from "@catalog/api-client";

import { t } from "./texts";

/** Campo del formulario → el texto de su error. */
export type FieldErrors = Record<string, string>;

/**
 * La clave del campo según el `loc` del error: `whatsapp`, `instagram`,
 * `message_templates.<caso>`, `on_order_notice`, `template` (vista previa) o, en las
 * listas de «Cómo comprar», `topics.<i>.<campo>` y `faq.<i>.<campo>`.
 */
export function fieldKey(loc: ValidationError["loc"]): string {
  const path = loc.filter((part) => part !== "body").map(String);
  if (path[0] === "contact_channels" && path[1]) return path[1];
  if (path[0] === "topics" || path[0] === "faq") return path.slice(0, 3).join(".");
  return path.slice(0, 2).join(".");
}

function message(field: string, error: ValidationError): string {
  const ctx = (error.ctx ?? {}) as Record<string, unknown>;
  switch (error.type) {
    case "unknown_variable":
      return t("admin.contact.error.unknownVariable", { variable: `{${String(ctx.variable)}}` });
    case "string_pattern_mismatch":
      if (field === "whatsapp") return t("admin.contact.error.whatsapp");
      if (field === "instagram") return t("admin.contact.error.instagram");
      return t("admin.contact.error.invalid");
    case "blank":
    case "string_too_short":
    case "missing":
      return t("admin.contact.error.required");
    case "section_heading":
      return t("admin.howToBuy.error.sectionHeading");
    case "unclosed_fence":
      return t("admin.howToBuy.error.unclosedFence");
    case "multiline":
      return t("admin.howToBuy.error.multiline");
    case "string_too_long":
      return t("admin.contact.error.tooLong", { max: String(ctx.max_length ?? "") });
    default:
      return t("admin.contact.error.invalid");
  }
}

/** Un error por campo (el primero que da la API). */
export function fieldErrors(detail: ValidationError[]): FieldErrors {
  const errors: FieldErrors = {};
  for (const error of detail) {
    const field = fieldKey(error.loc);
    errors[field] ??= message(field, error);
  }
  return errors;
}

/** Inserta `text` en lugar de la selección y devuelve el texto nuevo y dónde queda el cursor. */
export function insertAt(
  value: string,
  text: string,
  start: number,
  end: number,
): { value: string; cursor: number } {
  return { value: value.slice(0, start) + text + value.slice(end), cursor: start + text.length };
}
