import Form from "next/form";
import Link from "next/link";

import {
  listingHref,
  MAX_SEARCH_LENGTH,
  SEARCH_PARAM,
  filterAndSortFields,
  withoutSearch,
  type Listing,
} from "@/lib/listing";
import { t } from "@/lib/texts";

// Caja de búsqueda del listado. Es un formulario GET: sin JS también funciona, y
// con JS Next navega sin recargar. Filtros y orden viajan como campos ocultos para
// que buscar no los pierda; las páginas cargadas no (una búsqueda nueva arranca de cero).
export function ListingSearch({ pathname, listing }: { pathname: string; listing: Listing }) {
  return (
    <div className="flex flex-col gap-2">
      <Form action={pathname} scroll={false} role="search" className="flex gap-2">
        <label htmlFor="listing-search" className="sr-only">
          {t("listing.search.label")}
        </label>
        <input
          // defaultValue no cambia al navegar: con otra búsqueda, el campo se rearma.
          key={listing.q ?? ""}
          id="listing-search"
          type="search"
          name={SEARCH_PARAM}
          defaultValue={listing.q}
          placeholder={t("listing.search.placeholder")}
          maxLength={MAX_SEARCH_LENGTH}
          enterKeyHint="search"
          className="h-11 min-w-0 flex-1 rounded-sm border border-border bg-surface px-3 text-base focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary md:text-sm"
        />
        {filterAndSortFields(listing).map(([name, value]) => (
          <input key={`${name}=${value}`} type="hidden" name={name} value={value} />
        ))}
        <button
          type="submit"
          className="h-11 shrink-0 rounded-sm bg-primary px-4 text-sm font-medium text-primary-contrast hover:opacity-90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
        >
          {t("listing.search.submit")}
        </button>
      </Form>
      {listing.q && (
        <Link
          href={listingHref(pathname, withoutSearch(listing))}
          scroll={false}
          className="self-start text-sm text-primary underline underline-offset-4"
        >
          {t("listing.search.clear")}
        </Link>
      )}
    </div>
  );
}
