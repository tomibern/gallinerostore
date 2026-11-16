import type { Inquiry } from "@/lib/api";
import { t } from "@/lib/texts";

import { InquiryButtons } from "./inquiry-buttons";
import { channelLabels, instagramSheetLabels } from "./inquiry-labels";

// Dónde está: el registro de consultas y los e2e lo distinguen por esto.
export type GeneralInquiryPlacement = "listing" | "not-found" | "how-to-buy" | "footer";

type Props = {
  // La consulta general por canal, armada por la API (`general_inquiries`).
  inquiries: Inquiry[];
  placement: GeneralInquiryPlacement;
  title?: string;
  text?: string;
  // «box»: recuadro con título y texto; «compact»: una línea y los botones (el pie).
  variant?: "box" | "compact";
};

// Consulta general («¿Buscás algo que no está?»): abre los mismos canales que la
// consulta de un producto, con la plantilla general. Sin canales, no se muestra.
export function GeneralInquiry({
  inquiries,
  placement,
  title = t("generalInquiry.title"),
  text = t("generalInquiry.text"),
  variant = "box",
}: Props) {
  if (inquiries.length === 0) return null;
  const buttons = (
    <InquiryButtons
      short={variant === "compact"}
      channels={inquiries.map((inquiry) => inquiry.channel)}
      inquiries={inquiries}
      labels={{
        channels: channelLabels(t("inquiry.channel.idle")),
        sheet: instagramSheetLabels(),
      }}
    />
  );

  if (variant === "compact") {
    return (
      <div data-testid="general-inquiry" data-placement={placement} className="flex flex-col gap-3">
        <p className="font-display text-lg font-semibold">{t("generalInquiry.footer")}</p>
        {buttons}
      </div>
    );
  }

  // En fila solo si el recuadro tiene lugar (no depende de la pantalla: en el 404 o
  // en la columna del listado puede ser angosto).
  return (
    <section data-testid="general-inquiry" data-placement={placement} className="@container">
      <div className="flex flex-col gap-4 rounded-lg border border-border bg-surface p-5 @2xl:flex-row @2xl:items-center @2xl:justify-between @2xl:p-6">
        <div className="flex flex-col gap-1">
          <h2 className="font-display text-xl font-bold uppercase md:text-2xl">{title}</h2>
          <p className="text-sm text-muted">{text}</p>
        </div>
        <div className="@2xl:w-md">{buttons}</div>
      </div>
    </section>
  );
}
