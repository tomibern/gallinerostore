"use client";

import { useState } from "react";

import type { Channel, Inquiry } from "@/lib/api";

import { InstagramSheet, type InstagramSheetLabels } from "./instagram-sheet";

export type InquiryActionsLabels = {
  // El caso arriba de los botones («Consultar disponibilidad») o la pista sin talle.
  action: string;
  // Por canal: corto en el celular («WhatsApp») y completo en escritorio y para
  // lectores de pantalla («Consultar disponibilidad por WhatsApp»).
  channels: Record<Channel, { short: string; long: string }>;
  sheet: InstagramSheetLabels;
};

type Props = {
  // Los canales que ofrece la tienda, en orden: se muestran aunque no se pueda
  // consultar todavía. Sin canales, no hay botones.
  channels: Channel[];
  // Las consultas listas (mensaje y link de la API); null, todavía no se puede
  // consultar (falta elegir talle) y los botones quedan deshabilitados.
  inquiries: Inquiry[] | null;
  // Para la etiqueta del caso (in_stock, out_of_stock, on_order…).
  status?: string;
  labels: InquiryActionsLabels;
  // Al abrir el chat de un canal (lo usa el registro de consultas).
  onInquiry?: (channel: Channel) => void;
};

const BUTTON =
  "font-display flex min-h-12 flex-1 items-center justify-center gap-2 rounded-md px-3 py-2 text-center leading-tight font-semibold transition-opacity";

// Botones de consulta. WhatsApp es un link común a wa.me con el mensaje: abre la app
// sin JavaScript ni esperas. Instagram abre la hoja con el mensaje visible. En el
// celular quedan fijos abajo; en escritorio, en su lugar.
export function InquiryActions({ channels, inquiries, status, labels, onInquiry }: Props) {
  const [sheet, setSheet] = useState<Inquiry | null>(null);
  if (channels.length === 0) return null;

  return (
    <div
      data-testid="inquiry-actions"
      className="fixed inset-x-0 bottom-0 z-30 flex flex-col gap-2 border-t border-border bg-surface px-4 pt-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] shadow-[0_-4px_12px_rgb(0_0_0/0.06)] md:static md:z-auto md:border-0 md:bg-transparent md:p-0 md:shadow-none"
    >
      <p
        data-testid="inquiry-action"
        data-status={inquiries ? (status ?? "") : ""}
        className="font-display text-sm font-semibold tracking-wide uppercase"
      >
        {labels.action}
      </p>
      <div className="flex gap-2">
        {channels.map((channel) => {
          const inquiry = inquiries?.find((i) => i.channel === channel);
          const { short, long } = labels.channels[channel];
          const text = (
            <>
              <span className="md:hidden">{short}</span>
              <span className="hidden md:inline">{long}</span>
            </>
          );
          const style = `${BUTTON} ${
            channel === "whatsapp"
              ? "bg-primary text-primary-contrast"
              : "border border-border bg-surface text-text"
          }`;
          if (!inquiry) {
            return (
              <button
                key={channel}
                type="button"
                disabled
                aria-label={long}
                data-channel={channel}
                className={`${style} cursor-not-allowed opacity-50`}
              >
                {text}
              </button>
            );
          }
          if (channel === "whatsapp") {
            return (
              <a
                key={channel}
                href={inquiry.url}
                target="_blank"
                rel="noopener noreferrer"
                aria-label={long}
                data-channel={channel}
                onClick={() => onInquiry?.(channel)}
                className={style}
              >
                {text}
              </a>
            );
          }
          return (
            <button
              key={channel}
              type="button"
              aria-label={long}
              aria-haspopup="dialog"
              data-channel={channel}
              onClick={() => setSheet(inquiry)}
              className={`${style} cursor-pointer`}
            >
              {text}
            </button>
          );
        })}
      </div>
      <InstagramSheet
        inquiry={sheet}
        labels={labels.sheet}
        onClose={() => setSheet(null)}
        onOpenChat={() => onInquiry?.("instagram")}
      />
    </div>
  );
}
