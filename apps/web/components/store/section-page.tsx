import type { Metadata } from "next";

import { getSectionListing, getStore, type Section } from "@/lib/api";
import { listingPageSize } from "@/lib/env";
import {
  hasFilters,
  listingHref,
  parseListing,
  parsePages,
  type SearchParams,
} from "@/lib/listing";
import { pageMetadata } from "@/lib/seo";
import { t, type TextKey } from "@/lib/texts";

import { DiagonalBand } from "./diagonal-band";
import { GeneralInquiry } from "./general-inquiry";
import { ListingFilters, SortOptions } from "./listing-filters";
import { ListingSearch } from "./listing-search";
import { ProductGrid } from "./product-grid";

export const SECTION_PATHS: Record<Section, string> = { stock: "/stock", on_order: "/encargue" };

const HEADINGS: Record<Section, { title: TextKey; description: TextKey }> = {
  stock: { title: "section.stock.title", description: "section.stock.description" },
  on_order: { title: "section.onOrder.title", description: "section.onOrder.description" },
};

export function sectionTitle(section: Section): string {
  return t(HEADINGS[section].title);
}

/** Título, descripción, canonical y Open Graph del listado de una sección. */
export async function sectionMetadata(section: Section): Promise<Metadata> {
  const store = await getStore();
  const title = sectionTitle(section);
  if (!store) return { title };
  return pageMetadata(store, {
    path: SECTION_PATHS[section],
    title,
    description: t(HEADINGS[section].description),
  });
}

// Listado de una sección: encabezado, filtros (chips arriba en el celular,
// barra lateral en escritorio), orden y grilla de tarjetas (2 columnas en el
// celular, 3 o 4 en escritorio). Búsqueda, filtros, orden y páginas cargadas salen
// de la URL. La búsqueda va arriba de todo, también en el celular.
export async function SectionPage({
  section,
  searchParams,
}: {
  section: Section;
  searchParams: SearchParams;
}) {
  const listing = parseListing(searchParams);
  const pathname = SECTION_PATHS[section];
  const pageSize = listingPageSize();
  // Todas las páginas que pide la URL en un pedido (5 × 20 entra en el tope de la API).
  const [store, result] = await Promise.all([
    getStore(),
    getSectionListing(section, listing, parsePages(searchParams) * pageSize),
  ]);
  const heading = HEADINGS[section];

  return (
    <main>
      <header className="bg-primary text-primary-contrast">
        <div className="mx-auto flex max-w-7xl flex-col gap-1 px-4 py-6 md:px-16 md:py-10">
          <h1 className="font-display text-4xl leading-none font-bold uppercase md:text-6xl">
            {t(heading.title)}
          </h1>
          <p className="text-sm md:text-base">{t(heading.description)}</p>
        </div>
      </header>
      <DiagonalBand className="h-3 md:h-4" />

      {!store || !result ? (
        <p className="py-12 text-center text-muted">{t("section.unavailable")}</p>
      ) : (
        <div className="mx-auto flex max-w-7xl flex-col gap-6 px-4 py-6 md:grid md:grid-cols-[13rem_1fr] md:gap-x-10 md:gap-y-6 md:px-16 md:py-10">
          <div className="md:col-span-2">
            <ListingSearch pathname={pathname} listing={listing} />
          </div>
          <ListingFilters
            pathname={pathname}
            listing={listing}
            facets={result.facets}
            store={store}
          />
          <div className="flex min-w-0 flex-col gap-4">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <p aria-live="polite" data-testid="product-count" className="text-sm text-muted">
                {result.total === 1
                  ? t("listing.count.one")
                  : t("listing.count.other", { count: result.total })}
              </p>
              <SortOptions pathname={pathname} listing={listing} />
            </div>
            {result.items.length === 0 ? (
              <p className="py-12 text-center text-muted">
                {listing.q
                  ? t("listing.search.empty", { q: listing.q })
                  : hasFilters(listing)
                    ? t("listing.empty")
                    : t("section.empty")}
              </p>
            ) : (
              <ProductGrid
                // Otro filtro u orden es otro listado: arranca de cero.
                key={listingHref(pathname, listing)}
                section={section}
                pathname={pathname}
                listing={listing}
                pageSize={pageSize}
                total={result.total}
                initial={{ items: result.items, hasMore: result.has_more }}
                store={store}
              />
            )}
            <GeneralInquiry inquiries={store.general_inquiries} placement="listing" />
          </div>
        </div>
      )}
    </main>
  );
}
