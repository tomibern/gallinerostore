import { describe, expect, it } from "vitest";

import type { ValidationError } from "@catalog/api-client";

import { fieldErrors, fieldKey, insertAt } from "./admin-settings";
import { t } from "./texts";

// El OpenAPI no tipa `ctx` (un objeto cualquiera): el test lo arma como lo manda la API.
function apiError(loc: string[], type: string, ctx?: Record<string, unknown>): ValidationError {
  return { loc, msg: "", type, ...(ctx && { ctx }) } as ValidationError;
}

describe("fieldKey", () => {
  it("lleva cada error de la API a su campo del formulario", () => {
    expect(fieldKey(["body", "contact_channels", "whatsapp", "number"])).toBe("whatsapp");
    expect(fieldKey(["body", "contact_channels", "instagram", "username"])).toBe("instagram");
    expect(fieldKey(["body", "message_templates", "on_order"])).toBe("message_templates.on_order");
    expect(fieldKey(["body", "on_order_notice"])).toBe("on_order_notice");
    expect(fieldKey(["body", "template"])).toBe("template");
    expect(fieldKey(["body", "topics", "2", "title"])).toBe("topics.2.title");
    expect(fieldKey(["body", "faq", "0", "answer"])).toBe("faq.0.answer");
  });
});

describe("fieldErrors", () => {
  it("explica por qué un texto de «Cómo comprar» no se puede guardar", () => {
    const errors = fieldErrors([
      apiError(["body", "topics", "0", "title"], "blank"),
      apiError(["body", "topics", "0", "text"], "section_heading"),
      apiError(["body", "faq", "1", "answer"], "unclosed_fence"),
    ]);

    expect(errors).toEqual({
      "topics.0.title": t("admin.contact.error.required"),
      "topics.0.text": t("admin.howToBuy.error.sectionHeading"),
      "faq.1.answer": t("admin.howToBuy.error.unclosedFence"),
    });
  });

  it("elige el texto del diccionario según el tipo de error", () => {
    const errors = fieldErrors([
      apiError(["body", "contact_channels", "whatsapp", "number"], "string_pattern_mismatch"),
      apiError(["body", "message_templates", "stock"], "unknown_variable", { variable: "talle" }),
      apiError(["body", "message_templates", "general"], "blank"),
    ]);

    expect(errors).toEqual({
      whatsapp: t("admin.contact.error.whatsapp"),
      "message_templates.stock": t("admin.contact.error.unknownVariable", { variable: "{talle}" }),
      "message_templates.general": t("admin.contact.error.required"),
    });
  });

  it("deja el primer error de cada campo", () => {
    const errors = fieldErrors([
      apiError(["body", "on_order_notice"], "string_too_long", { max_length: 2000 }),
      apiError(["body", "on_order_notice"], "otra_cosa"),
    ]);

    expect(errors).toEqual({
      on_order_notice: t("admin.contact.error.tooLong", { max: "2000" }),
    });
  });
});

describe("insertAt", () => {
  it("reemplaza la selección y deja el cursor después de lo insertado", () => {
    expect(insertAt("Hola  chau", "{size}", 5, 5)).toEqual({
      value: "Hola {size} chau",
      cursor: 11,
    });
    expect(insertAt("Hola XX", "{product}", 5, 7)).toEqual({ value: "Hola {product}", cursor: 14 });
  });
});
