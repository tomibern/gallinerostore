// Metadatos de las páginas de la tienda: título, descripción, canonical, Open
// Graph (la vista previa al compartir por WhatsApp o Instagram) y sitemap.
// Las rutas quedan relativas: Next las vuelve absolutas con metadataBase (SITE_URL).

import type { Metadata, MetadataRoute } from "next";

import type { ProductDetail, PublicStore } from "./api";
import { formatPrice } from "./money";
import { t } from "./texts";

type OpenGraph = NonNullable<Metadata["openGraph"]>;

// Tope del recorte de la descripción del producto en la descripción de la página.
const DESCRIPTION_EXCERPT = 120;

// Productos por pedido al recorrer el catálogo (el máximo que acepta la API) y
// tope de vueltas: 50.000 URLs, el límite de un sitemap.
const SITEMAP_PAGE_SIZE = 100;
const SITEMAP_MAX_PAGES = 500;

/** Ruta del detalle de un producto: el código va en minúsculas. */
export function productPath(code: string): string {
  return `/p/${code.toLowerCase()}`;
}

/**
 * Open Graph común a todas las páginas. Next no mezcla `openGraph` entre
 * segmentos (el de la página reemplaza entero al del layout), así que cada
 * página lo repite con esto.
 */
export function baseOpenGraph(store: PublicStore): OpenGraph {
  // OGP pide el idioma como «es_AR».
  return { siteName: store.name, locale: store.locale.replace("-", "_"), type: "website" };
}

/** Metadatos del layout raíz: URL base, plantilla de título y descripción de la tienda. */
export function rootMetadata(store: PublicStore | null, siteUrl: URL): Metadata {
  if (!store) return { metadataBase: siteUrl };
  return {
    metadataBase: siteUrl,
    title: {
      default: store.name,
      template: t("meta.titleTemplate", { store: store.name }),
    },
    // La heredan las páginas sin descripción propia (la 404).
    description: t("meta.home.description", { store: store.name }),
    openGraph: baseOpenGraph(store),
  };
}

/**
 * Metadatos de una página de la tienda. Sin `title` queda el de la tienda (la
 * home). El canonical y `og:url` van sin query: los filtros, las páginas cargadas
 * y `utm_source` no hacen otra página.
 */
export function pageMetadata(
  store: PublicStore,
  { path, title, description }: { path: string; title?: string; description: string },
): Metadata {
  return {
    ...(title && { title }),
    description,
    alternates: { canonical: path },
    openGraph: { ...baseOpenGraph(store), url: path, title: title ?? store.name, description },
  };
}

function excerpt(text: string): string {
  const flat = text.replace(/\s+/g, " ").trim();
  if (flat.length <= DESCRIPTION_EXCERPT) return flat;
  return `${flat.slice(0, DESCRIPTION_EXCERPT).trimEnd()}…`;
}

function productDescription(product: ProductDetail, store: PublicStore): string {
  const vars = {
    price: formatPrice(product.price, product.currency, store.locale, store.price_decimals),
    availability: t(`availability.${product.availability}`),
  };
  return product.description
    ? t("meta.product.descriptionWithText", { ...vars, text: excerpt(product.description) })
    : t("meta.product.description", vars);
}

/**
 * Metadatos del detalle: el nombre como `og:title` (WhatsApp pide el título sin
 * la marca, que va en `og:site_name`), el precio al principio de la descripción
 * (no hay etiqueta Open Graph estándar para el precio) y la portada de 1600 px.
 */
export function productMetadata(product: ProductDetail, store: PublicStore): Metadata {
  const path = productPath(product.code);
  const description = productDescription(product, store);
  const cover = product.images[0];
  return {
    title: product.name,
    description,
    alternates: { canonical: path },
    openGraph: {
      ...baseOpenGraph(store),
      url: path,
      title: product.name,
      description,
      ...(cover && {
        images: [{ url: cover.full, width: cover.width, height: cover.height, alt: cover.alt }],
      }),
    },
  };
}

type CodesPage = { items: { code: string }[]; has_more: boolean };

/**
 * Los códigos de todos los productos publicados, de a 100. Si un pedido falla,
 * falla todo: un sitemap sin productos le diría al buscador que ya no existen.
 */
export async function collectProductCodes(
  fetchPage: (offset: number, limit: number) => Promise<CodesPage>,
): Promise<string[]> {
  const codes: string[] = [];
  for (let page = 0; page < SITEMAP_MAX_PAGES; page++) {
    const { items, has_more } = await fetchPage(page * SITEMAP_PAGE_SIZE, SITEMAP_PAGE_SIZE);
    codes.push(...items.map((item) => item.code));
    if (!has_more) return codes;
  }
  throw new Error(`El catálogo tiene más de ${SITEMAP_MAX_PAGES} páginas de productos.`);
}

/** Entradas del sitemap: las rutas fijas y el detalle de cada producto, absolutas. */
export function sitemapEntries(
  siteUrl: URL,
  staticPaths: string[],
  codes: string[],
): MetadataRoute.Sitemap {
  return [...staticPaths, ...codes.map(productPath)].map((path) => ({
    url: new URL(path, siteUrl).href,
  }));
}
