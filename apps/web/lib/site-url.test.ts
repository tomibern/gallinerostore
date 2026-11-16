import { describe, expect, it } from "vitest";

import { parseSiteUrl } from "./site-url";

describe("parseSiteUrl", () => {
  it("usa localhost:3000 si no hay valor, igual que la API", () => {
    expect(parseSiteUrl(undefined).href).toBe("http://localhost:3000/");
    expect(parseSiteUrl("").href).toBe("http://localhost:3000/");
  });

  it("acepta una URL http o https", () => {
    expect(parseSiteUrl("https://tienda.test").href).toBe("https://tienda.test/");
    expect(parseSiteUrl("http://192.168.0.10:3000/").href).toBe("http://192.168.0.10:3000/");
  });

  it("rechaza un valor que no es una URL", () => {
    expect(() => parseSiteUrl("tienda.test")).toThrow(/SITE_URL/);
  });

  it("rechaza otros protocolos", () => {
    expect(() => parseSiteUrl("ftp://tienda.test")).toThrow(/SITE_URL/);
  });
});
