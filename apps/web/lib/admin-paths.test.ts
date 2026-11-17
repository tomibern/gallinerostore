import { describe, expect, it } from "vitest";

import { afterLoginPath } from "./admin-paths";

describe("afterLoginPath", () => {
  it("vuelve a la página del panel que se pidió", () => {
    expect(afterLoginPath("/admin/metricas")).toBe("/admin/metricas");
    expect(afterLoginPath("/admin/productos?filtro=ocultos")).toBe(
      "/admin/productos?filtro=ocultos",
    );
  });

  it("sin destino, o con uno que no es del panel, va a Productos", () => {
    expect(afterLoginPath(null)).toBe("/admin/productos");
    expect(afterLoginPath("")).toBe("/admin/productos");
    expect(afterLoginPath("https://otro.sitio/admin")).toBe("/admin/productos");
    expect(afterLoginPath("//otro.sitio/admin")).toBe("/admin/productos");
    expect(afterLoginPath("/stock")).toBe("/admin/productos");
    expect(afterLoginPath("/administrador")).toBe("/admin/productos");
  });

  it("nunca vuelve al login", () => {
    expect(afterLoginPath("/admin/login")).toBe("/admin/productos");
  });
});
