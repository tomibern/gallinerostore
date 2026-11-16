import Link from "next/link";

import { DiagonalBand } from "@/components/store/diagonal-band";
import { HomeCarousel } from "@/components/store/home/home-carousel";
import { ProductCard } from "@/components/store/product-card";
import { StoreLogo } from "@/components/store/store-logo";
import { getFeatured, getStore, type HomeBlock } from "@/lib/api";
import { homeBlockText, t, type TextKey } from "@/lib/texts";

// Accesos grandes a las secciones del catálogo.
const ACCESS: { href: string; title: TextKey; description: TextKey }[] = [
  { href: "/stock", title: "section.stock.title", description: "section.stock.description" },
  {
    href: "/encargue",
    title: "section.onOrder.title",
    description: "section.onOrder.description",
  },
];

// Home: portada, accesos a las secciones, destacados y bloques con carrusel.
// Sin destacados (o si la API no responde) ese bloque no aparece; un bloque sin
// fotos, tampoco.
export default async function Home() {
  const [store, featured] = await Promise.all([getStore(), getFeatured()]);
  const tagline = t("store.tagline");

  return (
    <main>
      <section className="mx-auto flex max-w-7xl flex-col items-start gap-4 px-4 py-12 md:flex-row md:items-center md:gap-8 md:px-16 md:py-20">
        <StoreLogo className="size-24 md:size-40" />
        <div className="flex flex-col items-start gap-3">
          <h1 className="font-display bg-primary px-3 py-1.5 text-5xl leading-none font-bold text-primary-contrast uppercase md:text-8xl">
            {store?.name}
          </h1>
          {tagline && (
            <p className="font-display bg-primary-strong px-3 py-1 text-base font-semibold text-primary-contrast uppercase md:text-[22px]">
              {tagline}
            </p>
          )}
        </div>
      </section>
      <DiagonalBand className="h-5 md:h-7" />

      <nav aria-label={t("home.access.label")} className="mx-auto max-w-7xl px-4 py-8 md:px-16">
        <ul className="grid gap-3 md:grid-cols-2 md:gap-6">
          {ACCESS.map(({ href, title, description }) => (
            <li key={href}>
              <Link
                href={href}
                className="flex min-h-32 flex-col justify-end gap-1 rounded-md bg-primary p-5 text-primary-contrast transition-colors hover:bg-primary-strong md:min-h-48 md:p-8"
              >
                <span className="font-display text-4xl leading-none font-bold uppercase md:text-6xl">
                  {t(title)}
                </span>
                <span className="text-sm md:text-base">{t(description)}</span>
              </Link>
            </li>
          ))}
        </ul>
      </nav>

      {store && featured && featured.length > 0 && (
        <section
          aria-labelledby="featured-title"
          className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-8 md:px-16 md:py-12"
        >
          <h2
            id="featured-title"
            className="font-display text-3xl leading-none font-bold uppercase md:text-5xl"
          >
            {t("home.featured.title")}
          </h2>
          <ul
            data-testid="featured"
            className="grid grid-cols-2 gap-3 md:grid-cols-3 md:gap-6 lg:grid-cols-4"
          >
            {featured.map((product) => (
              <ProductCard key={product.code} product={product} store={store} />
            ))}
          </ul>
        </section>
      )}

      {store?.home_blocks
        .filter((block) => block.slides.length > 0)
        .map((block) => (
          <HomeBlockCarousel key={block.key} block={block} />
        ))}
    </main>
  );
}

function HomeBlockCarousel({ block }: { block: HomeBlock }) {
  const total = block.slides.length;
  const numbers = block.slides.map((_, i) => i + 1);

  return (
    <HomeCarousel
      slides={block.slides}
      title={homeBlockText(block.key, "title")}
      text={homeBlockText(block.key, "text")}
      labels={{
        region: t("home.carousel.label"),
        role: t("home.carousel.role"),
        slideRole: t("home.carousel.slideRole"),
        stop: t("home.carousel.stop"),
        start: t("home.carousel.start"),
        picker: t("home.carousel.picker"),
        pick: numbers.map((n) => t("home.carousel.pick", { n })),
        slide: numbers.map((n) => t("home.carousel.slide", { n, total })),
      }}
    />
  );
}
