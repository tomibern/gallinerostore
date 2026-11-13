import { describe, expect, it } from "vitest";

import { createTranslator } from "./translator";

// Diccionario de ejemplo: los tests no dependen de los textos reales del núcleo.
const core = {
  "product.story.title": "Historia del producto",
  "nav.stock": "En stock",
} as const;

describe("createTranslator", () => {
  it("usa el reemplazo del cliente cuando pisa una clave", () => {
    const t = createTranslator(core, { "product.story.title": "Historia de la prenda" });
    expect(t("product.story.title")).toBe("Historia de la prenda");
  });

  it("usa el texto del núcleo para las claves sin reemplazo", () => {
    const t = createTranslator(core, { "product.story.title": "Historia de la prenda" });
    expect(t("nav.stock")).toBe("En stock");
  });

  it("usa solo el núcleo cuando el cliente no tiene archivo de reemplazos", () => {
    const t = createTranslator(core, null);
    expect(t("product.story.title")).toBe("Historia del producto");
  });

  it("ignora los reemplazos que no son texto", () => {
    const t = createTranslator(core, { "product.story.title": 42, "nav.stock": null });
    expect(t("product.story.title")).toBe("Historia del producto");
    expect(t("nav.stock")).toBe("En stock");
  });

  it("completa las variables del texto", () => {
    const t = createTranslator({ "footer.rights": "© {year} {store}" }, null);
    expect(t("footer.rights", { year: 2026, store: "Tienda" })).toBe("© 2026 Tienda");
  });
});
