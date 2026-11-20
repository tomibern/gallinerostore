import { describe, expect, it } from "vitest";

import { formatPrice, parsePrice, priceInput } from "./money";

// Intl separa el símbolo con un espacio duro; lo normalizamos para comparar.
const normalize = (text: string) => text.replace(/ /g, " ");

describe("formatPrice", () => {
  it("muestra pesos sin decimales a partir de centavos", () => {
    expect(normalize(formatPrice(4_500_000, "ARS", "es-AR", 0))).toBe("$ 45.000");
  });

  it("muestra los decimales que pide la configuración", () => {
    expect(normalize(formatPrice(1999, "USD", "en-US", 2))).toBe("$19.99");
  });

  it("respeta monedas sin unidad menor", () => {
    expect(normalize(formatPrice(500, "JPY", "ja-JP", 0))).toBe("￥500");
  });
});

describe("parsePrice", () => {
  it("pasa los pesos tipeados a centavos", () => {
    expect(parsePrice("45000", "ARS", "es-AR", 0)).toBe(4_500_000);
  });

  it("acepta los separadores de miles del idioma, el símbolo y espacios", () => {
    expect(parsePrice("45.000", "ARS", "es-AR", 0)).toBe(4_500_000);
    expect(parsePrice(" $ 1.250.000 ", "ARS", "es-AR", 0)).toBe(125_000_000);
  });

  it("no acepta decimales si la tienda no los muestra", () => {
    expect(parsePrice("45000,50", "ARS", "es-AR", 0)).toBeNull();
  });

  it("acepta los decimales que muestra la tienda", () => {
    expect(parsePrice("45000,5", "ARS", "es-AR", 2)).toBe(4_500_050);
    expect(parsePrice("19.99", "USD", "en-US", 2)).toBe(1999);
    expect(parsePrice("19.999", "USD", "en-US", 2)).toBeNull();
  });

  it("usa la unidad menor de la moneda", () => {
    expect(parsePrice("500", "JPY", "ja-JP", 0)).toBe(500);
  });

  it("rechaza lo que no es un precio", () => {
    for (const typed of ["", "abc", "-100", "4.50", "45..000", "1e5"]) {
      expect(parsePrice(typed, "ARS", "es-AR", 0)).toBeNull();
    }
  });
});

describe("priceInput", () => {
  it("muestra el precio como se tipea, sin símbolo ni miles", () => {
    expect(priceInput(4_500_000, "ARS", "es-AR", 0)).toBe("45000");
    expect(priceInput(1999, "USD", "en-US", 2)).toBe("19.99");
  });

  it("vuelve al mismo precio al leerlo", () => {
    const shown = priceInput(4_500_050, "ARS", "es-AR", 2);
    expect(parsePrice(shown, "ARS", "es-AR", 2)).toBe(4_500_050);
  });
});
