import type { Metadata } from "next";
import Link from "next/link";

import { GeneralInquiry } from "@/components/store/general-inquiry";
import { SECTION_PATHS, sectionTitle } from "@/components/store/section-page";
import { getStore, type Section } from "@/lib/api";
import { t } from "@/lib/texts";

const SECTIONS: Section[] = ["stock", "on_order"];

export const metadata: Metadata = {
  title: t("notFound.title"),
  description: t("notFound.text"),
};

// 404 de la tienda, con encabezado y pie: un producto oculto, archivado o que no
// existe, y cualquier URL sin ruta (ver [...rest]). Lleva a las secciones y a la
// consulta general. getStore() reusa el pedido del layout.
export default async function StoreNotFound() {
  const store = await getStore();

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
      {store && (
        <div className="mt-8 w-full text-left">
          <GeneralInquiry inquiries={store.general_inquiries} placement="not-found" />
        </div>
      )}
    </main>
  );
}
