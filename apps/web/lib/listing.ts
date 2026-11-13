// Filtros y orden del listado. Todo vive en la query string (así un listado
// filtrado se comparte) y se pasa tal cual a GET /products.

export const FILTERS = ["category", "version", "collection", "tag", "size"] as const;
export type FilterName = (typeof FILTERS)[number];

export const SORTS = ["manual", "newest", "price_asc", "price_desc"] as const;
export type Sort = (typeof SORTS)[number];

export type Listing = Record<FilterName, string[]> & { sort?: Sort };

export type SearchParams = Record<string, string | string[] | undefined>;

function toArray(value: string | string[] | undefined): string[] {
  if (value === undefined) return [];
  return Array.isArray(value) ? value : [value];
}

/** Lo que pide la URL. Un orden desconocido se descarta (no rompe el listado). */
export function parseListing(params: SearchParams): Listing {
  const sort = SORTS.find((s) => s === toArray(params.sort)[0]);
  return {
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

/** La URL del listado con ese estado: claves repetidas, como las lee la API. */
export function listingHref(pathname: string, listing: Listing): string {
  const query = new URLSearchParams();
  for (const name of FILTERS) for (const value of listing[name]) query.append(name, value);
  if (listing.sort && listing.sort !== "manual") query.set("sort", listing.sort);
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

export function withoutFilters(listing: Listing): Listing {
  return { ...parseListing({}), sort: listing.sort };
}
