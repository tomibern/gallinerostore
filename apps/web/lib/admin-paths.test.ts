import { describe, expect, it } from "vitest";

import { afterLoginPath, newPasswordProblem } from "./admin-paths";

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

  it("nunca vuelve a una pantalla sin sesión", () => {
    expect(afterLoginPath("/admin/login")).toBe("/admin/productos");
    expect(afterLoginPath("/admin/recuperar")).toBe("/admin/productos");
    expect(afterLoginPath("/admin/elegir-contrasena")).toBe("/admin/productos");
  });
});

describe("newPasswordProblem", () => {
  it("acepta 10 caracteres o más que coinciden, sin reglas de composición", () => {
    expect(newPasswordProblem("diez-chars", "diez-chars")).toBeNull();
    expect(newPasswordProblem("aaaaaaaaaaaa", "aaaaaaaaaaaa")).toBeNull();
  });

  it("avisa si es corta antes que si no coincide", () => {
    expect(newPasswordProblem("nueve-chr", "otra")).toBe("short");
  });

  it("avisa si la repetición no coincide", () => {
    expect(newPasswordProblem("una-clave-larga", "una-clave-larg")).toBe("mismatch");
  });
});
