import type { Channel } from "@/lib/api";
import { t } from "@/lib/texts";

import type { InquiryButtonsLabels } from "./inquiry-buttons";

const CHANNELS: Channel[] = ["whatsapp", "instagram"];

// Textos de los botones por canal: el nombre corto y el completo, con la acción
// («Consultar disponibilidad por WhatsApp»). Se arman en el servidor.
export function channelLabels(action: string): InquiryButtonsLabels["channels"] {
  return Object.fromEntries(
    CHANNELS.map((channel) => {
      const short = t(`inquiry.channel.${channel}`);
      return [channel, { short, long: t("inquiry.channel.long", { action, channel: short }) }];
    }),
  ) as InquiryButtonsLabels["channels"];
}

export function instagramSheetLabels(): InquiryButtonsLabels["sheet"] {
  return {
    title: t("inquiry.sheet.title"),
    text: t("inquiry.sheet.text"),
    copy: t("inquiry.sheet.copy"),
    copied: t("inquiry.sheet.copied"),
    copyFailed: t("inquiry.sheet.copyFailed"),
    open: t("inquiry.sheet.open"),
    close: t("inquiry.sheet.close"),
  };
}

// Los textos de un caso: la acción arriba de los botones y los botones por canal
// (que pueden decir otra acción, como «Consultar» cuando todavía falta el talle).
export function caseLabels(action: string, buttonAction = action) {
  return { action, channels: channelLabels(buttonAction) };
}
