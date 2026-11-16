"use client";

import { useEffect, useEffectEvent, useRef, useState } from "react";

import type { ProductList, ProductListItem, PublicStore, Section } from "@/lib/api";
import { getListingPage } from "@/lib/browser-api";
import {
  appendPage,
  listingHref,
  PAGES_PARAM,
  pagesToLoad,
  parsePages,
  type Listing,
} from "@/lib/listing";
import { t } from "@/lib/texts";

import { ProductCard } from "./product-card";

type Loaded = { items: ProductListItem[]; hasMore: boolean };
// `listing` es la URL del listado sin `paginas`: a qué listado pertenece.
type Remembered = Loaded & { listing: string };

// Con cuánta anticipación se pide la página siguiente, antes de llegar al final.
const PRELOAD_MARGIN = "0px 0px 600px 0px";

// Lo que sumó el navegador, por URL del listado (con `paginas`). Al volver del
// detalle, Next no vuelve a renderizar en el servidor: restaura la página que
// tenía en caché (solo las primeras) y este componente se monta de nuevo. Si
// arranca con lo de acá, el listado ya tiene el largo de antes cuando el
// navegador restaura el scroll. Se escribe solo al sumar una página (nunca en
// el render ni en el servidor) y vive lo que dura el documento.
const loadedByUrl = new Map<string, Remembered>();

function currentUrl(): string {
  return window.location.pathname + window.location.search;
}

/** La URL actual sin `paginas`, para saber si sigue siendo este listado. */
function currentListing(): string {
  const query = new URLSearchParams(window.location.search);
  query.delete(PAGES_PARAM);
  const search = query.toString();
  return search ? `${window.location.pathname}?${search}` : window.location.pathname;
}

/**
 * Lo cargado antes para la URL actual, si es de este listado. En una navegación
 * con un link, el componente nuevo se monta antes de que cambie la URL: sin
 * comparar el listado, arrancaría con los productos de otro filtro u orden.
 */
function remembered(listing: string): Loaded | undefined {
  const entry = loadedByUrl.get(currentUrl());
  return entry?.listing === listing ? entry : undefined;
}

/** Guarda en la entrada del historial dónde estaba el scroll, para el respaldo. */
function saveScroll() {
  window.history.replaceState({ ...window.history.state, scrollY: window.scrollY }, "");
}

type Props = {
  section: Section;
  pathname: string;
  listing: Listing;
  pageSize: number;
  total: number;
  initial: Loaded;
  store: PublicStore;
};

// Grilla del listado con scroll infinito: suma una página al acercarse al final
// o con «Ver más» (por si la carga automática no anda, como en el navegador de
// Instagram). La URL lleva cuántas páginas hay (`paginas`, con replaceState), así
// una recarga o un link las trae del servidor.
export function ProductGrid({
  section,
  pathname,
  listing,
  pageSize,
  total,
  initial,
  store,
}: Props) {
  const base = listingHref(pathname, listing);
  const [loaded, setLoaded] = useState<Loaded>(() =>
    typeof window === "undefined" ? initial : (remembered(base) ?? initial),
  );
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");
  const busy = useRef(false);
  const sentinel = useRef<HTMLDivElement>(null);
  const scrollAfterLoad = useRef<number | null>(null);

  /** Suma una página a lo cargado, la recuerda por URL y pone `paginas` en la URL. */
  function remember(page: ProductList): Loaded {
    const items = appendPage(loaded.items, page.items);
    const next = { items, hasMore: page.has_more };
    const url = listingHref(pathname, listing, pagesToLoad(items.length, pageSize));
    loadedByUrl.set(url, { ...next, listing: base });
    // Si mientras tanto se fue a otro listado, la URL ya no es la de este.
    if (currentListing() === base) window.history.replaceState(window.history.state, "", url);
    return next;
  }

  function fetchMore(limit: number): Promise<ProductList> {
    return getListingPage(section, listing, { offset: loaded.items.length, limit });
  }

  async function load(limit: number) {
    if (busy.current) return;
    busy.current = true;
    setStatus("loading");
    try {
      setLoaded(remember(await fetchMore(limit)));
      setStatus("idle");
    } catch {
      setStatus("error");
    } finally {
      busy.current = false;
    }
  }

  const onNearEnd = useEffectEvent(() => void load(pageSize));
  const restore = useEffectEvent(() => {
    // Respaldo: la URL pide más páginas de las que hay (se perdió lo cargado).
    // Se piden las que faltan y se vuelve a donde estaba el scroll.
    const query = new URLSearchParams(window.location.search);
    const wanted = parsePages({ [PAGES_PARAM]: query.get(PAGES_PARAM) ?? undefined });
    const missing = wanted * pageSize - loaded.items.length;
    if (missing <= 0 || !loaded.hasMore) return;
    const { scrollY } = (window.history.state ?? {}) as { scrollY?: unknown };
    if (typeof scrollY === "number") scrollAfterLoad.current = scrollY;
    busy.current = true;
    fetchMore(missing)
      .then((page) => setLoaded(remember(page)))
      .catch(() => setStatus("error"))
      .finally(() => {
        busy.current = false;
      });
  });

  useEffect(() => {
    restore();
    window.addEventListener("pagehide", saveScroll);
    return () => window.removeEventListener("pagehide", saveScroll);
  }, []);

  useEffect(() => {
    if (scrollAfterLoad.current === null) return;
    window.scrollTo(0, scrollAfterLoad.current);
    scrollAfterLoad.current = null;
  }, [loaded]);

  // Se vuelve a observar después de cada carga: si el final sigue a la vista
  // (pantallas altas), el observer avisa de nuevo y se pide otra página.
  useEffect(() => {
    const target = sentinel.current;
    if (!target || !loaded.hasMore || status !== "idle") return;
    if (!("IntersectionObserver" in window)) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) onNearEnd();
      },
      { rootMargin: PRELOAD_MARGIN },
    );
    observer.observe(target);
    return () => observer.disconnect();
  }, [loaded, status]);

  return (
    <>
      <ul
        data-testid="products"
        data-page-size={pageSize}
        // Antes de ir al detalle, por si al volver hay que restaurar a mano.
        onClickCapture={saveScroll}
        className="grid grid-cols-2 gap-3 md:grid-cols-3 md:gap-5 lg:grid-cols-4"
      >
        {loaded.items.map((product) => (
          <ProductCard key={product.code} product={product} store={store} />
        ))}
      </ul>
      <div ref={sentinel} aria-hidden="true" />
      <div className="flex flex-col items-center gap-3 py-4">
        <p role="status" className="text-center text-sm text-muted">
          {status === "loading" && t("listing.loading")}
          {status === "error" && t("listing.loadError")}
          {status === "idle" && loaded.items.length > initial.items.length && (
            <span className="sr-only">
              {t("listing.shown", { shown: loaded.items.length, total })}
            </span>
          )}
        </p>
        {loaded.hasMore && (
          <button
            type="button"
            onClick={() => void load(pageSize)}
            disabled={status === "loading"}
            className="rounded-md border border-border bg-surface px-6 py-2.5 font-medium transition-colors hover:border-primary disabled:opacity-60"
          >
            {t("listing.loadMore")}
          </button>
        )}
      </div>
    </>
  );
}
