import type { FaqItem } from "@/lib/api";

import { StoreMarkdown } from "./store-markdown";

// Preguntas frecuentes como acordeón nativo: cada pregunta es un <details> con su
// encabezado dentro del <summary>. Comparten `name`, así abrir una cierra la otra
// (donde el navegador no lo soporta, quedan varias abiertas). Sin JavaScript.
export function FaqAccordion({ faq }: { faq: FaqItem[] }) {
  return (
    <div className="divide-y divide-border border-y border-border">
      {faq.map(({ question, answer_md }) => (
        <details key={question} name="faq" className="group">
          <summary className="flex min-h-12 cursor-pointer list-none items-center justify-between gap-4 py-3 [&::-webkit-details-marker]:hidden">
            <h3 className="font-display text-lg font-semibold">{question}</h3>
            <span
              aria-hidden="true"
              className="font-display text-2xl leading-none text-primary group-open:hidden"
            >
              +
            </span>
            <span
              aria-hidden="true"
              className="font-display hidden text-2xl leading-none text-primary group-open:inline"
            >
              −
            </span>
          </summary>
          <div data-testid="faq-answer" className="pb-4 text-muted">
            <StoreMarkdown>{answer_md}</StoreMarkdown>
          </div>
        </details>
      ))}
    </div>
  );
}
