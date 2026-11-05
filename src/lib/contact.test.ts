import { describe, expect, it } from "vitest";
import { buildInstagramLink, buildWhatsAppLink } from "./contact";

describe("buildWhatsAppLink", () => {
  it("limpia el número y agrega un mensaje genérico", () => {
    const url = new URL(buildWhatsAppLink("+54 9 11 1234-5678"));
    expect(url.pathname).toBe("/5491112345678");
    expect(url.searchParams.get("text")).toContain("consulta");
  });

  it("incluye nombre y talle de la prenda", () => {
    const url = new URL(buildWhatsAppLink("5491112345678", { name: "Titular 1986", size: "M" }));
    expect(url.searchParams.get("text")).toBe(
      "Hola! Me interesa la camiseta Titular 1986 talle M. ¿Está disponible?",
    );
  });

  it("falla con un número vacío", () => {
    expect(() => buildWhatsAppLink("abc")).toThrow();
  });
});

describe("buildInstagramLink", () => {
  it("acepta el usuario con o sin @", () => {
    expect(buildInstagramLink("@gallinerostore14")).toBe("https://instagram.com/gallinerostore14");
  });
});
