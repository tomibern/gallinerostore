"use client";

import type { Channel, Inquiry, SizeStatus } from "@/lib/api";

import { InquiryButtons, type InquiryButtonsLabels, type InquiryTrack } from "./inquiry-buttons";

export type InquiryActionsLabels = InquiryButtonsLabels & {
  // El caso arriba de los botones («Consultar disponibilidad») o la pista sin talle.
  action: string;
};

type Props = {
  // Los canales que ofrece la tienda, en orden. Sin canales, no hay botones.
  channels: Channel[];
  // Las consultas del talle elegido; null, todavía no hay talle.
  inquiries: Inquiry[] | null;
  // Para la etiqueta del caso (in_stock, out_of_stock, on_order…).
  status?: SizeStatus;
  labels: InquiryActionsLabels;
  // Al abrir el chat de un canal (lo usa el registro de consultas).
  onInquiry?: (channel: Channel) => void;
  // La consulta que se registra al abrir el chat (#34).
  track?: InquiryTrack;
};

// Consulta del detalle: el caso y los botones por canal. En el celular quedan fijos
// abajo; en escritorio, en su lugar.
export function InquiryActions({ channels, inquiries, status, labels, onInquiry, track }: Props) {
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
      <InquiryButtons
        channels={channels}
        inquiries={inquiries}
        labels={labels}
        onInquiry={onInquiry}
        track={track}
      />
    </div>
  );
}
