// Lo que el listado de productos del admin calcula a partir de la URL y de lo que
// devuelve la API. Sin imports del servidor.

import type { AdminFilter, AdminProductListItem } from "./admin-api";
import { SEARCH_PARAM } from "./listing";

// Parámetros de la URL del listado: `q` (búsqueda, el mismo de la tienda) y `filtro`.
export { SEARCH_PARAM };
export const FILTER_PARAM = "filtro";

// El filtro de la API por su nombre en la URL. «Todos» no va en la URL.
const FILTER_SLUGS: Record<AdminFilter, string | null> = {
  all: null,
  stock: "stock",
  on_order: "encargue",
  sold_out: "agotados",
  draft: "borradores",
  hidden: "ocultos",
  archived: "archivados",
};

export const ADMIN_FILTERS = Object.keys(FILTER_SLUGS) as AdminFilter[];

/** El filtro de la URL; uno que no existe es «Todos». */
export function parseFilter(slug: string | null): AdminFilter {
  const found = ADMIN_FILTERS.find((filter) => FILTER_SLUGS[filter] === slug);
  return found ?? "all";
}

/** La URL del listado con esa búsqueda y ese filtro. */
export function adminListingHref(pathname: string, q: string, filter: AdminFilter): string {
  const query = new URLSearchParams();
  const search = q.trim();
  if (search) query.set(SEARCH_PARAM, search);
  const slug = FILTER_SLUGS[filter];
  if (slug) query.set(FILTER_PARAM, slug);
  const qs = query.toString();
  return qs ? `${pathname}?${qs}` : pathname;
}

/** Agotado: producto de stock sin talles disponibles. Lo dice la disponibilidad que
 * calcula la API, con la regla del catálogo público. */
export function isSoldOut(product: AdminProductListItem): boolean {
  return product.availability === "sold_out" || product.availability === "sold_out_on_order";
}

/** Los talles en corto para la tarjeta del celular. */
export type SizeSummary =
  | { kind: "none" }
  | { kind: "on_order"; first: string; last: string }
  | { kind: "stock"; available: number; total: number };

export function sizeSummary(product: AdminProductListItem): SizeSummary {
  const { sizes } = product;
  if (sizes.length === 0) return { kind: "none" };
  if (sizes.every((size) => size.status === "on_order")) {
    return { kind: "on_order", first: sizes[0].label, last: sizes[sizes.length - 1].label };
  }
  const available = sizes.filter((size) => size.status === "in_stock").length;
  return { kind: "stock", available, total: sizes.length };
}
