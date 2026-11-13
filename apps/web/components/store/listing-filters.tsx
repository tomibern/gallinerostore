import Link from "next/link";

import type { FacetValue, ProductFacets, PublicStore } from "@/lib/api";
import {
  hasFilters,
  listingHref,
  SORTS,
  toggleFilter,
  withoutFilters,
  withSort,
  type FilterName,
  type Listing,
} from "@/lib/listing";
import { t } from "@/lib/texts";

type Props = { pathname: string; listing: Listing };

// Los filtros son links (funcionan sin JS y cada estado tiene su URL). El valor
// elegido se marca con aria-current. En el celular, cada filtro es una fila de
// chips con scroll horizontal; en escritorio, una barra lateral.
export function ListingFilters({
  pathname,
  listing,
  facets,
  store,
}: Props & { facets: ProductFacets; store: PublicStore }) {
  const groups: { name: FilterName; label: string; values: FacetValue[] }[] = [
    { name: "category", label: t("listing.filter.category"), values: facets.categories },
    { name: "collection", label: store.collection_label, values: facets.collections },
    { name: "version", label: t("listing.filter.version"), values: facets.versions },
    { name: "size", label: t("listing.filter.size"), values: facets.sizes },
    { name: "tag", label: t("listing.filter.tag"), values: facets.tags },
  ];

  return (
    <aside aria-label={t("listing.filters")} className="flex flex-col gap-4 md:gap-6">
      {groups
        .filter((group) => group.values.length > 0)
        .map((group) => (
          <div
            key={group.name}
            role="group"
            aria-labelledby={`filter-${group.name}`}
            data-filter={group.name}
          >
            <h2
              id={`filter-${group.name}`}
              className="mb-2 font-display text-sm font-bold tracking-wide uppercase"
            >
              {group.label}
            </h2>
            <ul className="-mx-4 flex gap-2 overflow-x-auto px-4 pb-1 md:mx-0 md:flex-wrap md:overflow-visible md:px-0">
              {group.values.map((value) => (
                <li key={value.value} className="shrink-0">
                  <Chip
                    href={listingHref(pathname, toggleFilter(listing, group.name, value.value))}
                    active={listing[group.name].includes(value.value)}
                    count={value.count}
                  >
                    {value.name}
                  </Chip>
                </li>
              ))}
            </ul>
          </div>
        ))}
      {hasFilters(listing) && (
        <Link
          href={listingHref(pathname, withoutFilters(listing))}
          scroll={false}
          className="self-start text-sm text-primary underline underline-offset-4"
        >
          {t("listing.clear")}
        </Link>
      )}
    </aside>
  );
}

export function SortOptions({ pathname, listing }: Props) {
  const current = listing.sort ?? "manual";
  return (
    <div role="group" aria-labelledby="listing-sort" className="flex flex-col gap-2">
      <h2 id="listing-sort" className="sr-only">
        {t("listing.sort")}
      </h2>
      <ul className="-mx-4 flex gap-2 overflow-x-auto px-4 pb-1 md:mx-0 md:flex-wrap md:px-0">
        {SORTS.map((sort) => (
          <li key={sort} className="shrink-0">
            <Chip href={listingHref(pathname, withSort(listing, sort))} active={sort === current}>
              {t(`listing.sort.${sort}`)}
            </Chip>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Chip({
  href,
  active,
  count,
  children,
}: {
  href: string;
  active: boolean;
  count?: number;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      scroll={false}
      aria-current={active ? "true" : undefined}
      className={`flex min-h-9 items-center gap-1.5 rounded-full border px-3 text-sm whitespace-nowrap ${
        active
          ? "border-primary bg-primary text-primary-contrast"
          : "border-border bg-surface hover:border-primary"
      }`}
    >
      {children}
      {count !== undefined && (
        <span aria-hidden="true" className={active ? "opacity-80" : "text-muted"}>
          {count}
        </span>
      )}
    </Link>
  );
}
