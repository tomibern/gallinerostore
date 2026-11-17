"use client";

import { usePathname } from "next/navigation";
import { useState } from "react";

import type { Channel, Inquiry } from "@/lib/api";
import { type EventFields, pageFromPath, trackEvent } from "@/lib/events";

import { InstagramSheet, type InstagramSheetLabels } from "./instagram-sheet";

export type InquiryButtonsLabels = {
  // Por canal: corto en el celular («WhatsApp») y completo en escritorio y para
  // lectores de pantalla («Consultar disponibilidad por WhatsApp»).
  channels: Record<Channel, { short: string; long: string }>;
  sheet: InstagramSheetLabels;
};

// Qué consulta registrar al abrir el chat (datos, no una función: la consulta general
// se arma en el servidor). Sin `page`, la consulta general toma la de la ruta.
export type InquiryTrack =
  | Omit<Extract<EventFields, { type: "contact_click" }>, "channel">
  | (Omit<Extract<EventFields, { type: "general_contact_click" }>, "channel" | "page"> & {
      page?: Extract<EventFields, { type: "general_contact_click" }>["page"];
    });

type Props = {
  // Los canales que ofrece la tienda, en orden: se muestran aunque no se pueda
  // consultar todavía. Sin canales, no hay botones.
  channels: Channel[];
  // Las consultas listas (mensaje y link de la API); null, todavía no se puede
  // consultar y los botones quedan deshabilitados.
  inquiries: Inquiry[] | null;
  labels: InquiryButtonsLabels;
  // Al abrir el chat de un canal (lo usa el registro de consultas).
  onInquiry?: (channel: Channel) => void;
  // La consulta que se registra al abrir el chat (#34).
  track?: InquiryTrack;
  // Siempre el nombre corto a la vista (donde falta lugar, como el pie); el
  // completo queda para lectores de pantalla.
  short?: boolean;
};

const BUTTON =
  "font-display flex min-h-12 flex-1 items-center justify-center gap-2 rounded-md px-3 py-2 text-center leading-tight font-semibold transition-opacity";

// Un botón por canal, sin posición propia (la pone quien lo usa). WhatsApp es un
// link común a wa.me con el mensaje: abre la app sin JavaScript ni esperas.
// Instagram abre la hoja con el mensaje visible.
export function InquiryButtons({
  channels,
  inquiries,
  labels,
  onInquiry,
  track,
  short = false,
}: Props) {
  const [sheet, setSheet] = useState<Inquiry | null>(null);
  const pathname = usePathname();
  if (channels.length === 0) return null;

  // Cuenta al tocar el link que abre el chat, no al abrir la hoja de Instagram.
  const inquire = (channel: Channel) => {
    if (track?.type === "contact_click") trackEvent({ ...track, channel });
    if (track?.type === "general_contact_click") {
      trackEvent({ ...track, channel, page: track.page ?? pageFromPath(pathname) });
    }
    onInquiry?.(channel);
  };

  return (
    <>
      <div className="flex gap-2">
        {channels.map((channel) => {
          const inquiry = inquiries?.find((i) => i.channel === channel);
          const { short: name, long } = labels.channels[channel];
          const text = short ? (
            name
          ) : (
            <>
              <span className="md:hidden">{name}</span>
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
                onClick={() => inquire(channel)}
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
        onOpenChat={() => inquire("instagram")}
      />
    </>
  );
}
