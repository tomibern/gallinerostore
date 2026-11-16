import Link from "next/link";

import { SECTION_PATHS, sectionTitle } from "@/components/store/section-page";
import type { Section } from "@/lib/api";
import { t } from "@/lib/texts";

const SECTIONS: Section[] = ["stock", "on_order"];

// 404 de la tienda, con encabezado y pie: un producto oculto, archivado o que no
// existe, y cualquier URL sin ruta (ver [...rest]). Lleva a las secciones.
export default function StoreNotFound() {
  return (
    <main className="mx-auto flex max-w-xl flex-col items-center gap-4 px-4 py-16 text-center md:py-24">
      <h1 className="font-display text-3xl font-bold md:text-4xl">{t("notFound.title")}</h1>
      <p className="text-muted">{t("notFound.text")}</p>
      <nav aria-label={t("notFound.sections")} className="mt-4 flex flex-col gap-3 sm:flex-row">
        {SECTIONS.map((section) => (
          <Link
            key={section}
            href={SECTION_PATHS[section]}
            className="font-display rounded-md bg-primary px-5 py-3 font-semibold tracking-wide text-primary-contrast uppercase hover:bg-primary-strong"
          >
            {sectionTitle(section)}
          </Link>
        ))}
      </nav>
    </main>
  );
}
