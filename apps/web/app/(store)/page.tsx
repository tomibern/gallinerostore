import { DiagonalBand } from "@/components/store/diagonal-band";
import { getStore } from "@/lib/api";
import { t } from "@/lib/texts";

// Home mínima: solo el layout de la tienda. La completa el ticket de Home
// (portada, accesos a las secciones, destacados y bloques con carrusel).
export default async function Home() {
  const store = await getStore();
  const tagline = t("store.tagline");

  return (
    <main>
      <section className="mx-auto flex max-w-7xl flex-col items-start gap-3 px-4 py-12 md:px-16 md:py-20">
        <h1 className="font-display bg-primary px-3 py-1.5 text-5xl leading-none font-bold text-primary-contrast uppercase md:text-8xl">
          {store?.name}
        </h1>
        {tagline && (
          <p className="font-display bg-primary-strong px-3 py-1 text-base font-semibold text-primary-contrast uppercase md:text-[22px]">
            {tagline}
          </p>
        )}
      </section>
      <DiagonalBand className="h-5 md:h-7" />
    </main>
  );
}
