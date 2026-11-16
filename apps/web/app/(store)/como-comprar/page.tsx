import type { Metadata } from "next";

import { DiagonalBand } from "@/components/store/diagonal-band";
import { FaqAccordion } from "@/components/store/faq-accordion";
import { GeneralInquiry } from "@/components/store/general-inquiry";
import { StoreMarkdown } from "@/components/store/store-markdown";
import { getStore } from "@/lib/api";
import { t } from "@/lib/texts";

// Mínimo: el título y la descripción completos los arma el SEO de la tienda.
export const metadata: Metadata = {
  title: t("howToBuy.title"),
  description: t("howToBuy.description"),
};

// «Cómo comprar»: pagos, envíos, entregas y encargues (Markdown que edita el admin),
// las preguntas frecuentes como acordeón y, al final, la consulta general. El layout
// ya resolvió que la tienda responde; getStore() reusa ese pedido.
export default async function HowToBuyPage() {
  const store = await getStore();
  const howToBuy = store?.how_to_buy_md.trim() ?? "";
  const faqIntro = store?.faq_intro_md ?? "";
  const faq = store?.faq ?? [];
  const hasFaq = faqIntro !== "" || faq.length > 0;

  return (
    <main>
      <header className="bg-primary text-primary-contrast">
        <div className="mx-auto flex max-w-3xl flex-col gap-1 px-4 py-6 md:py-10">
          <h1 className="font-display text-4xl leading-none font-bold uppercase md:text-6xl">
            {t("howToBuy.title")}
          </h1>
          <p className="text-sm md:text-base">{t("howToBuy.description")}</p>
        </div>
      </header>
      <DiagonalBand className="h-3 md:h-4" />

      <div className="mx-auto flex max-w-3xl flex-col gap-10 px-4 py-8 md:py-12">
        {howToBuy === "" && !hasFaq ? (
          <p className="text-muted">{t("howToBuy.empty")}</p>
        ) : (
          howToBuy !== "" && (
            <section>
              <StoreMarkdown>{howToBuy}</StoreMarkdown>
            </section>
          )
        )}

        {hasFaq && (
          <section aria-labelledby="faq-title" className="flex flex-col gap-4">
            <h2 id="faq-title" className="font-display text-2xl font-bold uppercase md:text-3xl">
              {t("howToBuy.faq")}
            </h2>
            {faqIntro && <StoreMarkdown>{faqIntro}</StoreMarkdown>}
            {faq.length > 0 && <FaqAccordion faq={faq} />}
          </section>
        )}

        <GeneralInquiry
          inquiries={store?.general_inquiries ?? []}
          placement="how-to-buy"
          title={t("howToBuy.questions.title")}
          text={t("howToBuy.questions.text")}
        />
      </div>
    </main>
  );
}
