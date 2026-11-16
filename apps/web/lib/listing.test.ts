import { describe, expect, it } from "vitest";

import {
  appendPage,
  listingHref,
  MAX_PAGES,
  parsePageSize,
  pagesLoaded,
  parseListing,
  parsePages,
  toggleFilter,
} from "./listing";

describe("parsePages", () => {
  it("es 1 sin el parámetro", () => {
    expect(parsePages({})).toBe(1);
  });

  it("lee un entero", () => {
    expect(parsePages({ paginas: "3" })).toBe(3);
  });

  it("recorta al máximo", () => {
    expect(parsePages({ paginas: "999" })).toBe(MAX_PAGES);
  });

  it.each(["abc", "0", "-2", "2.5", "", "1e3"])("vuelve a 1 con «%s»", (value) => {
    expect(parsePages({ paginas: value })).toBe(1);
  });

  it("toma el primero si viene repetido", () => {
    expect(parsePages({ paginas: ["2", "4"] })).toBe(2);
  });
});

describe("listingHref con páginas", () => {
  const listing = parseListing({ category: "remeras", sort: "newest" });

  it("suma paginas a los filtros y el orden", () => {
    expect(listingHref("/stock", listing, 3)).toBe("/stock?category=remeras&sort=newest&paginas=3");
  });

  it("omite paginas=1, así la URL limpia sigue siendo la canónica", () => {
    expect(listingHref("/stock", listing, 1)).toBe("/stock?category=remeras&sort=newest");
    expect(listingHref("/stock", parseListing({}), 1)).toBe("/stock");
  });

  it("cambiar un filtro descarta las páginas", () => {
    const parsed = parseListing({ category: "remeras", paginas: "3" });
    expect(listingHref("/stock", toggleFilter(parsed, "tag", "titular"))).toBe(
      "/stock?category=remeras&tag=titular",
    );
  });
});

describe("parsePageSize", () => {
  it("es 20 por defecto", () => {
    expect(parsePageSize(undefined)).toBe(20);
  });

  it("lee un entero entre 1 y 20", () => {
    expect(parsePageSize("3")).toBe(3);
  });

  it.each(["0", "abc", "21", "-1"])("vuelve a 20 con «%s»", (value) => {
    expect(parsePageSize(value)).toBe(20);
  });
});

describe("pagesLoaded", () => {
  it("cuenta las páginas que entran en los productos cargados", () => {
    expect(pagesLoaded(20, 20)).toBe(1);
    expect(pagesLoaded(40, 20)).toBe(2);
    // La última página puede venir incompleta.
    expect(pagesLoaded(45, 20)).toBe(3);
  });

  it("nunca es menos de 1", () => {
    expect(pagesLoaded(0, 20)).toBe(1);
  });
});

describe("appendPage", () => {
  const item = (code: string) => ({ code });

  it("suma la página al final", () => {
    expect(appendPage([item("A"), item("B")], [item("C")])).toEqual([
      item("A"),
      item("B"),
      item("C"),
    ]);
  });

  it("no repite un producto que ya estaba (el listado cambió entre páginas)", () => {
    expect(appendPage([item("A"), item("B")], [item("B"), item("C")])).toEqual([
      item("A"),
      item("B"),
      item("C"),
    ]);
  });
});
