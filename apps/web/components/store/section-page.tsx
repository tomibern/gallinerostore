import { getSectionListing, getStore, type Section } from "@/lib/api";
import { hasFilters, parseListing, type SearchParams } from "@/lib/listing";
import { t, type TextKey } from "@/lib/texts";

import { DiagonalBand } from "./diagonal-band";
import { ListingFilters, SortOptions } from "./listing-filters";
import { ProductCard } from "./product-card";

const PATHS: Record<Section, string> = { stock: "/stock", on_order: "/encargue" };

const HEADINGS: Record<Section, { title: TextKey; description: TextKey }> = {
  stock: { title: "section.stock.title", description: "section.stock.description" },
  on_order: { title: "section.onOrder.title", description: "section.onOrder.description" },
};

export function sectionTitle(section: Section): string {
  return t(HEADINGS[section].title);
}

// Listado de una sección: encabezado, filtros (chips arriba en el celular,
// barra lateral en escritorio), orden y grilla de tarjetas (2 columnas en el
// celular, 3 o 4 en escritorio). Filtros y orden salen de la URL.
export async function SectionPage({
  section,
  searchParams,
}: {
  section: Section;
  searchParams: SearchParams;
}) {
  const listing = parseListing(searchParams);
  const pathname = PATHS[section];
  const [store, result] = await Promise.all([getStore(), getSectionListing(section, listing)]);
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
        <div className="mx-auto flex max-w-7xl flex-col gap-6 px-4 py-6 md:grid md:grid-cols-[13rem_1fr] md:gap-10 md:px-16 md:py-10">
          <ListingFilters
            pathname={pathname}
            listing={listing}
            facets={result.facets}
            store={store}
          />
          <div className="flex min-w-0 flex-col gap-4">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <p aria-live="polite" data-testid="product-count" className="text-sm text-muted">
                {result.items.length === 1
                  ? t("listing.count.one")
                  : t("listing.count.other", { count: result.items.length })}
              </p>
              <SortOptions pathname={pathname} listing={listing} />
            </div>
            {result.items.length === 0 ? (
              <p className="py-12 text-center text-muted">
                {hasFilters(listing) ? t("listing.empty") : t("section.empty")}
              </p>
            ) : (
              <ul
                data-testid="products"
                className="grid grid-cols-2 gap-3 md:grid-cols-3 md:gap-5 lg:grid-cols-4"
              >
                {result.items.map((product) => (
                  <ProductCard key={product.code} product={product} store={store} />
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </main>
  );
}
