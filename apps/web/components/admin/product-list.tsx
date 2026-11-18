"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { getAdminProducts, type AdminFilter, type AdminProductListItem } from "@/lib/admin-api";
import { ADMIN_LOGIN, adminProductPath } from "@/lib/admin-paths";
import {
  ADMIN_FILTERS,
  adminListingHref,
  FILTER_PARAM,
  isSoldOut,
  parseFilter,
  SEARCH_PARAM,
  sizeSummary,
} from "@/lib/admin-products";
import { DEFAULT_PAGE_SIZE as PAGE_SIZE, MAX_SEARCH_LENGTH } from "@/lib/listing";
import { formatPrice } from "@/lib/money";
import { t } from "@/lib/texts";
import { cn } from "@/lib/utils";

// Cuánto se espera después de la última tecla antes de buscar.
const SEARCH_DELAY_MS = 300;

type LoadedPage = { items: AdminProductListItem[]; hasMore: boolean; total: number };
// `loaded` es null si el pedido falló.
type PageResult = { key: string; loaded: LoadedPage | null };

export type PriceFormat = { locale: string; decimals: number };
type Price = (product: AdminProductListItem) => string;

const SIZE_STYLE: Record<AdminProductListItem["sizes"][number]["status"], string> = {
  in_stock: "border border-accent font-bold",
  out_of_stock: "border border-dashed border-border font-semibold text-muted line-through",
  on_order: "border border-border font-semibold text-muted",
};

const STATUS_STYLE: Record<AdminProductListItem["status"], string> = {
  published: "border border-border bg-panel text-text",
  draft: "border border-dashed border-muted bg-surface text-muted",
  hidden: "border border-border bg-bg text-muted",
  archived: "border border-border bg-bg text-muted line-through decoration-1",
};

function StatusBadges({ product }: { product: AdminProductListItem }) {
  return (
    <span className="flex flex-wrap items-center gap-1.5">
      <span
        data-status={product.status}
        className={cn(
          "px-2 py-1 text-xs font-bold whitespace-nowrap",
          STATUS_STYLE[product.status],
        )}
      >
        {t(`admin.products.status.${product.status}`)}
      </span>
      {isSoldOut(product) && (
        <span
          data-sold-out=""
          className="bg-primary px-2 py-1 text-xs font-bold whitespace-nowrap text-primary-contrast"
        >
          {t("admin.products.soldOut")}
        </span>
      )}
    </span>
  );
}

function Sizes({ product }: { product: AdminProductListItem }) {
  if (product.sizes.length === 0) {
    return <span className="text-sm text-muted">{t("admin.products.noSizes")}</span>;
  }
  return (
    <ul className="flex flex-wrap gap-1">
      {product.sizes.map((size) => (
        <li
          key={size.label}
          data-size-status={size.status}
          className={cn("px-1.5 py-0.5 text-[11px]", SIZE_STYLE[size.status])}
        >
          {size.status === "out_of_stock" ? (
            <>
              <span aria-hidden="true">{size.label}</span>
              <span className="sr-only">
                {t("admin.products.outOfStock", { size: size.label })}
              </span>
            </>
          ) : (
            size.label
          )}
        </li>
      ))}
    </ul>
  );
}

function SizeSummaryText({ product }: { product: AdminProductListItem }) {
  const summary = sizeSummary(product);
  switch (summary.kind) {
    case "none":
      return t("admin.products.noSizes");
    case "on_order":
      return t("admin.products.sizesOnOrder", { first: summary.first, last: summary.last });
    case "stock":
      return t("admin.products.sizesCount", {
        available: summary.available,
        total: summary.total,
      });
  }
}

function FeaturedStar({ featured }: { featured: boolean }) {
  return (
    <svg
      role="img"
      aria-label={t(featured ? "admin.products.featured" : "admin.products.notFeatured")}
      data-featured={featured}
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill={featured ? "currentColor" : "none"}
      stroke="currentColor"
      strokeWidth="2"
      strokeLinejoin="round"
      className={featured ? "text-primary" : "text-border"}
    >
      <path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z" />
    </svg>
  );
}

function Cover({ product, size }: { product: AdminProductListItem; size: string }) {
  return (
    <span className={cn("block shrink-0 overflow-hidden bg-bg", size)}>
      {product.cover && (
        // Las fotos ya llegan redimensionadas y en WebP desde la API.
        <Image
          src={product.cover.thumb}
          alt=""
          width={product.cover.width}
          height={product.cover.height}
          unoptimized
          className="size-full object-cover"
        />
      )}
    </span>
  );
}

function ProductTable({ items, price }: { items: AdminProductListItem[]; price: Price }) {
  const th = "px-2 py-2.5 text-left text-xs font-bold tracking-wider whitespace-nowrap uppercase";
  const td = "border-b border-border px-2 py-2.5 align-middle text-sm";
  return (
    <div className="hidden overflow-x-auto bg-surface px-4 pt-2 pb-4 md:block">
      <table className="w-full border-collapse">
        <thead>
          <tr className="border-b-2 border-accent text-muted">
            <th className={th}>{t("admin.products.column.product")}</th>
            <th className={th}>{t("admin.products.column.section")}</th>
            <th className={th}>{t("admin.products.column.sizes")}</th>
            <th className={th}>{t("admin.products.column.price")}</th>
            <th className={th}>{t("admin.products.column.status")}</th>
            <th className={th} title={t("admin.products.column.featuredHint")}>
              {t("admin.products.column.featured")}
            </th>
          </tr>
        </thead>
        <tbody>
          {items.map((product) => (
            // Toda la fila lleva al editor: el link del producto la cubre entera.
            <tr
              key={product.code}
              data-code={product.code}
              data-featured={product.featured}
              className="relative hover:bg-bg"
            >
              <td className={td}>
                <Link
                  href={adminProductPath(product.code)}
                  className="flex items-center gap-2.5 after:absolute after:inset-0 hover:text-primary"
                >
                  <Cover product={product} size="size-12" />
                  <span className="flex flex-col gap-0.5">
                    <span className="font-semibold">{product.name}</span>
                    <span className="text-xs text-muted">{product.code}</span>
                  </span>
                </Link>
              </td>
              <td className={cn(td, "whitespace-nowrap")}>
                {t(`admin.products.section.${product.section}`)}
              </td>
              <td className={td}>
                <Sizes product={product} />
              </td>
              <td className={cn(td, "font-bold whitespace-nowrap")}>{price(product)}</td>
              <td className={td}>
                <StatusBadges product={product} />
              </td>
              <td className={td}>
                <FeaturedStar featured={product.featured} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ProductCards({ items, price }: { items: AdminProductListItem[]; price: Price }) {
  return (
    <ul className="flex flex-col md:hidden">
      {items.map((product) => {
        const href = adminProductPath(product.code);
        const meta = [product.code, t(`admin.products.section.${product.section}`)];
        if (product.featured) meta.push(t("admin.products.featured"));
        return (
          // Toda la tarjeta lleva al editor: el link del nombre la cubre entera.
          <li
            key={product.code}
            data-code={product.code}
            data-featured={product.featured}
            className="relative flex items-start gap-3 border-b border-border py-3.5"
          >
            <Cover product={product} size="size-16" />
            <div className="flex min-w-0 flex-1 flex-col gap-1">
              <Link
                href={href}
                className="leading-tight font-semibold after:absolute after:inset-0"
              >
                {product.name}
              </Link>
              <span className="text-xs text-muted">{meta.join(" · ")}</span>
              <span className="flex flex-wrap items-center gap-1.5">
                <StatusBadges product={product} />
                <span className="text-xs text-muted">
                  <SizeSummaryText product={product} />
                </span>
              </span>
            </div>
            <span className="text-sm font-bold whitespace-nowrap">{price(product)}</span>
          </li>
        );
      })}
    </ul>
  );
}

/**
 * Listado de productos del admin: búsqueda y filtro en la URL (`q` y `filtro`), tabla
 * en escritorio y tarjetas en el celular. Todavía de solo lectura: cada producto lleva
 * al editor.
 */
export function ProductList({ priceFormat }: { priceFormat: PriceFormat }) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const q = params.get(SEARCH_PARAM) ?? "";
  const filter = parseFilter(params.get(FILTER_PARAM));

  const [text, setText] = useState(q);
  // La búsqueda de la URL para la que vale el campo: si la URL cambia por otro lado
  // (atrás/adelante), el campo la sigue.
  const [textSyncedWithQ, setTextSyncedWithQ] = useState(q);
  if (textSyncedWithQ !== q) {
    setTextSyncedWithQ(q);
    setText(q);
  }
  const [attempt, setAttempt] = useState(0);
  // Lo cargado lleva la clave del pedido (búsqueda, filtro e intento): si no coincide
  // con la actual, la página nueva todavía está cargando.
  const key = `${filter}|${attempt}|${q}`;
  const [result, setResult] = useState<PageResult | null>(null);
  const [loadingMore, setLoadingMore] = useState(false);
  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const price: Price = (product) =>
    formatPrice(product.price, product.currency, priceFormat.locale, priceFormat.decimals);

  const toLogin = useCallback(() => {
    const next = window.location.pathname + window.location.search;
    router.replace(`${ADMIN_LOGIN}?next=${encodeURIComponent(next)}`);
  }, [router]);

  // La primera página, cada vez que cambian la búsqueda o el filtro de la URL.
  useEffect(() => {
    let active = true;
    getAdminProducts({ q, filter, offset: 0, limit: PAGE_SIZE })
      .then((page) => {
        if (!active) return;
        if (!page) return toLogin();
        setResult({
          key,
          loaded: { items: page.items, hasMore: page.has_more, total: page.total },
        });
      })
      .catch(() => {
        if (active) setResult({ key, loaded: null });
      });
    return () => {
      active = false;
    };
  }, [key, q, filter, toLogin]);

  useEffect(
    () => () => {
      if (searchTimer.current) clearTimeout(searchTimer.current);
    },
    [],
  );

  const current = result?.key === key ? result : null;
  const loaded = current?.loaded ?? null;
  const failed = current !== null && loaded === null;

  function replaceListingUrl(nextQ: string, nextFilter: AdminFilter) {
    if (searchTimer.current) clearTimeout(searchTimer.current);
    router.replace(adminListingHref(pathname, nextQ, nextFilter), { scroll: false });
  }

  function onSearch(value: string) {
    setText(value);
    if (searchTimer.current) clearTimeout(searchTimer.current);
    searchTimer.current = setTimeout(() => replaceListingUrl(value, filter), SEARCH_DELAY_MS);
  }

  async function loadMore() {
    if (!loaded || loadingMore) return;
    setLoadingMore(true);
    try {
      const page = await getAdminProducts({
        q,
        filter,
        offset: loaded.items.length,
        limit: PAGE_SIZE,
      });
      if (!page) return toLogin();
      const known = new Set(loaded.items.map((item) => item.code));
      setResult({
        key,
        loaded: {
          items: [...loaded.items, ...page.items.filter((item) => !known.has(item.code))],
          hasMore: page.has_more,
          total: page.total,
        },
      });
    } catch {
      setResult({ key, loaded: null });
    } finally {
      setLoadingMore(false);
    }
  }

  return (
    <div className="flex flex-col gap-4 md:gap-5">
      <div className="flex flex-col gap-2.5 md:flex-row md:items-center md:justify-between">
        <label className="flex h-12 items-center gap-2 border border-border bg-surface px-3 md:w-80 md:shrink-0">
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            aria-hidden="true"
            className="text-muted"
          >
            <circle cx="11" cy="11" r="7" />
            <path d="M20 20l-4-4" />
          </svg>
          <input
            type="search"
            value={text}
            onChange={(event) => onSearch(event.target.value)}
            placeholder={t("admin.products.searchPlaceholder")}
            aria-label={t("admin.products.search")}
            maxLength={MAX_SEARCH_LENGTH}
            className="min-w-0 flex-1 bg-transparent text-base outline-none placeholder:text-muted"
          />
        </label>
        <div
          role="group"
          aria-label={t("admin.products.filters")}
          className="-mx-4 flex gap-2 overflow-x-auto px-4 pb-1 md:order-first md:mx-0 md:flex-wrap md:px-0 md:pb-0"
        >
          {ADMIN_FILTERS.map((option) => (
            <button
              key={option}
              type="button"
              aria-pressed={option === filter}
              onClick={() => replaceListingUrl(text, option)}
              className={cn(
                "min-h-10 shrink-0 border px-3.5 text-sm font-semibold",
                option === filter
                  ? "border-accent bg-accent text-on-accent"
                  : "border-border bg-surface text-text hover:border-accent",
              )}
            >
              {t(`admin.products.filter.${option}`)}
            </button>
          ))}
        </div>
      </div>

      {failed ? (
        <div role="alert" className="flex flex-col items-start gap-3">
          <p>{t("admin.products.error")}</p>
          <Button variant="outline" onClick={() => setAttempt((n) => n + 1)}>
            {t("admin.retry")}
          </Button>
        </div>
      ) : !loaded ? (
        <p role="status" className="text-muted">
          {t("admin.products.loading")}
        </p>
      ) : loaded.items.length === 0 ? (
        <p role="status" className="text-muted">
          {q.trim() ? t("admin.products.noResults", { q: q.trim() }) : t("admin.products.empty")}
        </p>
      ) : (
        <>
          <p role="status" data-total={loaded.total} className="text-sm text-muted">
            {loaded.total === 1
              ? t("admin.products.totalOne")
              : t("admin.products.total", { count: loaded.total })}
          </p>
          <ProductTable items={loaded.items} price={price} />
          <ProductCards items={loaded.items} price={price} />
          {loaded.hasMore && (
            <Button
              variant="outline"
              className="self-center"
              disabled={loadingMore}
              onClick={loadMore}
            >
              {t("admin.products.loadMore")}
            </Button>
          )}
        </>
      )}
    </div>
  );
}
