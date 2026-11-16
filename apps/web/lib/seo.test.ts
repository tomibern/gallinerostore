import { describe, expect, it } from "vitest";

import type { ProductDetail, PublicStore } from "./api";
import { formatPrice } from "./money";
import {
  baseOpenGraph,
  collectProductCodes,
  pageMetadata,
  productMetadata,
  productPath,
  rootMetadata,
  sitemapEntries,
} from "./seo";
import { t } from "./texts";

const store = {
  name: "Tienda de prueba",
  locale: "es-AR",
  currency: "ARS",
  price_decimals: 0,
} as PublicStore;

const cover = {
  full: "/media/products/ABC-001/1-1600.webp",
  thumb: "/media/products/ABC-001/1-400.webp",
  alt: "Frente de la remera",
  width: 1600,
  height: 1200,
};

function product(overrides: Partial<ProductDetail> = {}): ProductDetail {
  return {
    code: "ABC-001",
    name: "Remera básica",
    price: 2_500_000,
    currency: "ARS",
    availability: "in_stock",
    description: null,
    images: [cover],
    ...overrides,
  } as ProductDetail;
}

describe("productPath", () => {
  it("lleva el código en minúsculas", () => {
    expect(productPath("ABC-001")).toBe("/p/abc-001");
  });
});

describe("baseOpenGraph", () => {
  it("pone el nombre de la tienda, el idioma con guion bajo y el tipo website", () => {
    expect(baseOpenGraph(store)).toEqual({
      siteName: "Tienda de prueba",
      locale: "es_AR",
      type: "website",
    });
  });
});

describe("rootMetadata", () => {
  const site = new URL("https://tienda.test");

  it("fija la URL base aunque la API no responda", () => {
    expect(rootMetadata(null, site)).toEqual({ metadataBase: site });
  });

  it("usa el nombre de la tienda en el título por defecto, la plantilla y la descripción", () => {
    const metadata = rootMetadata(store, site);
    expect(metadata.metadataBase).toBe(site);
    expect(metadata.title).toEqual({
      default: "Tienda de prueba",
      template: t("meta.titleTemplate", { store: "Tienda de prueba" }),
    });
    expect((metadata.title as { template: string }).template).toContain("%s");
    expect(metadata.description).toBe(t("meta.home.description", { store: "Tienda de prueba" }));
    expect(metadata.openGraph).toEqual(baseOpenGraph(store));
  });
});

describe("pageMetadata", () => {
  it("arma título, descripción, canonical y Open Graph de una página", () => {
    expect(
      pageMetadata(store, { path: "/stock", title: "En stock", description: "Para ya." }),
    ).toEqual({
      title: "En stock",
      description: "Para ya.",
      alternates: { canonical: "/stock" },
      openGraph: {
        ...baseOpenGraph(store),
        url: "/stock",
        title: "En stock",
        description: "Para ya.",
      },
    });
  });

  it("sin título deja el de la tienda (la home)", () => {
    const metadata = pageMetadata(store, { path: "/", description: "Catálogo." });
    expect(metadata.title).toBeUndefined();
    expect(metadata.openGraph).toMatchObject({ url: "/", title: "Tienda de prueba" });
  });
});

describe("productMetadata", () => {
  const price = formatPrice(2_500_000, "ARS", "es-AR", 0);

  it("usa el nombre del producto, sin la tienda, como título de Open Graph", () => {
    const metadata = productMetadata(product(), store);
    expect(metadata.title).toBe("Remera básica");
    expect(metadata.openGraph).toMatchObject({
      ...baseOpenGraph(store),
      title: "Remera básica",
    });
  });

  it("empieza la descripción con el precio y la disponibilidad", () => {
    const metadata = productMetadata(product(), store);
    expect(metadata.description).toBe(
      t("meta.product.description", { price, availability: t("availability.in_stock") }),
    );
    expect(metadata.description?.startsWith(price)).toBe(true);
    expect(metadata.openGraph?.description).toBe(metadata.description);
  });

  it("suma el principio de la descripción del producto, recortado", () => {
    const long = "Algodón peinado. ".repeat(20).trim();
    const metadata = productMetadata(product({ description: long }), store);
    expect(metadata.description?.startsWith(price)).toBe(true);
    expect(metadata.description).toContain("Algodón peinado.");
    expect(metadata.description!.length).toBeLessThan(long.length);
    expect(metadata.description?.endsWith("…")).toBe(true);
  });

  it("pone la portada de 1600 px con su tamaño y el canonical sin query", () => {
    const metadata = productMetadata(product(), store);
    expect(metadata.alternates).toEqual({ canonical: "/p/abc-001" });
    expect(metadata.openGraph).toMatchObject({
      url: "/p/abc-001",
      images: [{ url: cover.full, width: 1600, height: 1200, alt: cover.alt }],
    });
  });

  it("sin fotos no inventa una imagen", () => {
    const metadata = productMetadata(product({ images: [] }), store);
    expect(metadata.openGraph).not.toHaveProperty("images");
  });
});

describe("sitemapEntries", () => {
  it("vuelve absolutas las rutas fijas y las de cada producto", () => {
    const entries = sitemapEntries(
      new URL("https://tienda.test"),
      ["/", "/stock"],
      ["ABC-001", "XYZ-9"],
    );
    expect(entries).toEqual([
      { url: "https://tienda.test/" },
      { url: "https://tienda.test/stock" },
      { url: "https://tienda.test/p/abc-001" },
      { url: "https://tienda.test/p/xyz-9" },
    ]);
  });
});

describe("collectProductCodes", () => {
  it("recorre las páginas de a 100 hasta que no haya más", async () => {
    const offsets: number[] = [];
    const codes = await collectProductCodes(async (offset, limit) => {
      offsets.push(offset);
      expect(limit).toBe(100);
      return offset === 0
        ? { items: [{ code: "A" }, { code: "B" }], has_more: true }
        : { items: [{ code: "C" }], has_more: false };
    });
    expect(codes).toEqual(["A", "B", "C"]);
    expect(offsets).toEqual([0, 100]);
  });

  it("falla si la API falla, en vez de devolver una lista incompleta", async () => {
    await expect(
      collectProductCodes(async (offset) => {
        if (offset > 0) throw new Error("API caída");
        return { items: [{ code: "A" }], has_more: true };
      }),
    ).rejects.toThrow("API caída");
  });

  it("corta si la API nunca termina", async () => {
    await expect(
      collectProductCodes(async () => ({ items: [{ code: "A" }], has_more: true })),
    ).rejects.toThrow();
  });
});
