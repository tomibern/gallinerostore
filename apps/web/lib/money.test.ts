import { describe, expect, it } from "vitest";

import { formatPrice } from "./money";

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
