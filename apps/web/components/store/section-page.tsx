import { getSectionProducts, getStore, type Section } from "@/lib/api";
import { t, type TextKey } from "@/lib/texts";

import { DiagonalBand } from "./diagonal-band";
import { ProductCard } from "./product-card";

const HEADINGS: Record<Section, { title: TextKey; description: TextKey }> = {
  stock: { title: "section.stock.title", description: "section.stock.description" },
  on_order: { title: "section.onOrder.title", description: "section.onOrder.description" },
};

export function sectionTitle(section: Section): string {
  return t(HEADINGS[section].title);
}

// Listado de una sección: encabezado y grilla de tarjetas (2 columnas en el
// celular, 3 o 4 en escritorio).
export async function SectionPage({ section }: { section: Section }) {
  const [store, products] = await Promise.all([getStore(), getSectionProducts(section)]);
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

      <div className="mx-auto max-w-7xl px-4 py-6 md:px-16 md:py-10">
        {!store || !products ? (
          <p className="py-12 text-center text-muted">{t("section.unavailable")}</p>
        ) : products.length === 0 ? (
          <p className="py-12 text-center text-muted">{t("section.empty")}</p>
        ) : (
          <ul
            data-testid="products"
            className="grid grid-cols-2 gap-3 md:grid-cols-3 md:gap-5 lg:grid-cols-4"
          >
            {products.map((product) => (
              <ProductCard key={product.code} product={product} store={store} />
            ))}
          </ul>
        )}
      </div>
    </main>
  );
}
