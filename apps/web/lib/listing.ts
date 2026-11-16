// Búsqueda, filtros, orden y páginas del listado. Todo vive en la query string (así
// un listado filtrado se comparte). Búsqueda, filtros y orden se pasan tal cual a
// GET /products;
// `paginas` dice cuántas páginas cargó el navegador, para reconstruirlas al volver.

import type { Schemas } from "@catalog/api-client";

export type Sort = Schemas["ProductSort"];

export const FILTERS = ["category", "version", "collection", "tag", "size"] as const;
export type FilterName = (typeof FILTERS)[number];

// El orden por defecto («Destacados» en la UI) va primero.
export const SORTS = [
  "manual",
  "newest",
  "price_asc",
  "price_desc",
] as const satisfies readonly Sort[];

export type Listing = Record<FilterName, string[]> & { q?: string; sort?: Sort };

export const SEARCH_PARAM = "q";
// El largo máximo que acepta la API: lo que sobra se corta en vez de dar error.
export const MAX_SEARCH_LENGTH = 100;

export type SearchParams = Record<string, string | string[] | undefined>;

function toArray(value: string | string[] | undefined): string[] {
  if (value === undefined) return [];
  return Array.isArray(value) ? value : [value];
}

/** Lo que pide la URL. Un orden desconocido se descarta y una búsqueda vacía no
 * cuenta (no rompen el listado). */
export function parseListing(params: SearchParams): Listing {
  const sort = SORTS.find((s) => s === toArray(params.sort)[0]);
  const q = toArray(params[SEARCH_PARAM])[0]?.trim().slice(0, MAX_SEARCH_LENGTH);
  return {
    ...(q && { q }),
    category: toArray(params.category),
    version: toArray(params.version),
    collection: toArray(params.collection),
    tag: toArray(params.tag),
    size: toArray(params.size),
    ...(sort && { sort }),
  };
}

export function hasFilters(listing: Listing): boolean {
  return FILTERS.some((name) => listing[name].length > 0);
}

/**
 * La URL del listado con ese estado: claves repetidas, como las lee la API.
 * `paginas` solo va si es más de 1; un link que cambia filtros u orden no la
 * pasa, así vuelve a la primera página.
 */
export function listingHref(pathname: string, listing: Listing, pages = 1): string {
  const query = new URLSearchParams();
  if (listing.q) query.set(SEARCH_PARAM, listing.q);
  for (const [name, value] of searchFields(listing)) query.append(name, value);
  if (pages > 1) query.set(PAGES_PARAM, String(pages));
  const search = query.toString();
  return search ? `${pathname}?${search}` : pathname;
}

/** Suma o saca un valor de un filtro. */
export function toggleFilter(listing: Listing, name: FilterName, value: string): Listing {
  const values = listing[name];
  return {
    ...listing,
    [name]: values.includes(value) ? values.filter((v) => v !== value) : [...values, value],
  };
}

export function withSort(listing: Listing, sort: Sort): Listing {
  return { ...listing, sort };
}

/** Saca los filtros; la búsqueda y el orden quedan. */
export function withoutFilters(listing: Listing): Listing {
  return { ...parseListing({}), q: listing.q, sort: listing.sort };
}

export function withoutSearch(listing: Listing): Listing {
  return { ...listing, q: undefined };
}

/**
 * Lo que el formulario de búsqueda manda además de `q` (como campos ocultos):
 * filtros y orden, para que buscar no los pierda. Sin `paginas`: una búsqueda nueva
 * arranca en la primera página.
 */
export function searchFields(listing: Listing): [string, string][] {
  const fields: [string, string][] = [];
  for (const name of FILTERS) for (const value of listing[name]) fields.push([name, value]);
  if (listing.sort && listing.sort !== "manual") fields.push(["sort", listing.sort]);
  return fields;
}

// --- Páginas ------------------------------------------------------------------

export const PAGES_PARAM = "paginas";

// Tamaño de página por defecto y máximo: con MAX_PAGES páginas, el SSR las trae
// en un solo pedido sin pasar el tope de `limit` de la API (100).
export const DEFAULT_PAGE_SIZE = 20;
export const MAX_PAGES = 5;

function positiveInt(value: string | undefined): number | null {
  if (value === undefined || !/^\d+$/.test(value)) return null;
  const n = Number(value);
  return n >= 1 ? n : null;
}

/** Productos por página: un entero entre 1 y 20 (de LISTING_PAGE_SIZE), o 20. */
export function parsePageSize(value: string | undefined): number {
  const n = positiveInt(value);
  return n !== null && n <= DEFAULT_PAGE_SIZE ? n : DEFAULT_PAGE_SIZE;
}

/** Páginas que pide la URL: un entero de 1 a MAX_PAGES. Lo inválido vale 1. */
export function parsePages(params: SearchParams): number {
  const n = positiveInt(toArray(params[PAGES_PARAM])[0]);
  return n === null ? 1 : Math.min(n, MAX_PAGES);
}

/** En cuántas páginas entran los productos cargados (la última puede estar incompleta). */
export function pagesLoaded(loaded: number, size: number): number {
  return Math.max(1, Math.ceil(loaded / size));
}

/** Suma una página sin repetir productos (el listado puede cambiar entre dos pedidos). */
export function appendPage<T extends { code: string }>(items: T[], page: T[]): T[] {
  const seen = new Set(items.map((item) => item.code));
  return [...items, ...page.filter((item) => !seen.has(item.code))];
}
