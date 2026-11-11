import { getProducts, getStore, type ProductListItem, type PublicStore } from "@/lib/api";
import { formatPrice } from "@/lib/money";

import { HealthStatus } from "./health-status";

// Página de verificación de la tracer bullet: lista los productos publicados
// por SSR con el cliente generado. Sin diseño: eso llega en la fase 3.
export const dynamic = "force-dynamic";

export default async function Home() {
  const [store, products] = await Promise.all([getStore(), getProducts()]);

  return (
    <main className="mx-auto flex min-h-dvh max-w-3xl flex-col gap-6 px-4 py-10">
      <header className="flex flex-col items-center gap-4 text-center">
        <h1 className="font-display text-4xl font-bold uppercase tracking-tight text-primary sm:text-5xl">
          {store?.name ?? "Sin conexión con la API"}
        </h1>
        <p className="rounded-full border border-border bg-surface px-4 py-2 text-sm">
          {store && (
            <span className="text-muted">
              {store.currency} · {store.locale} ·{" "}
            </span>
          )}
          <HealthStatus />
        </p>
      </header>

      {store && products && (
        <ul className="grid gap-3 sm:grid-cols-2" data-testid="products">
          {products.map((product) => (
            <ProductCard key={product.code} product={product} store={store} />
          ))}
        </ul>
      )}
    </main>
  );
}

// Disponibilidad que ve el cliente: encargue, stock o sin stock. La van a
// reusar los filtros y la sección de cada producto en la fase 3.
type Availability = "on_order" | "in_stock" | "out_of_stock";

const AVAILABILITY_LABEL: Record<Availability, string> = {
  on_order: "Por encargue",
  in_stock: "En stock",
  out_of_stock: "Sin stock",
};

function availability(product: ProductListItem): Availability {
  if (product.sale_mode === "on_order") return "on_order";
  return product.out_of_stock ? "out_of_stock" : "in_stock";
}

function ProductCard({ product, store }: { product: ProductListItem; store: PublicStore }) {
  const price = formatPrice(product.price, product.currency, store.locale, store.price_decimals);
  const badge = AVAILABILITY_LABEL[availability(product)];

  return (
    <li
      className="flex flex-col gap-2 rounded-lg border border-border bg-surface p-4"
      data-code={product.code}
    >
      <div className="flex items-start justify-between gap-2">
        <h2 className="font-medium">{product.name}</h2>
        <span className="shrink-0 text-xs text-muted">{product.code}</span>
      </div>
      <p className="text-lg font-bold text-primary">{price}</p>
      <p className="text-xs uppercase tracking-wide text-accent">{badge}</p>
      <ul className="flex flex-wrap gap-1 text-sm">
        {product.sizes.map((size) => (
          <li
            key={size.label}
            className={`rounded border border-border px-2 ${size.in_stock ? "" : "text-muted line-through"}`}
          >
            {size.label}
          </li>
        ))}
      </ul>
    </li>
  );
}
