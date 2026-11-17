"use client";

import { useEffect } from "react";

import { type EventFields, trackEvent } from "@/lib/events";

type ViewEvent = Extract<EventFields, { type: "page_view" | "product_view" }>;

// Registra la visita al cargar la página en el navegador (no en el SSR: el prefetch y
// la mayoría de los bots no corren efectos). No dibuja nada. En desarrollo, el Strict
// Mode de React la manda dos veces; en producción, una.
export function TrackView({ event }: { event: ViewEvent }) {
  // Por valor: otro producto (o página) es otra visita; filtrar o cargar más, no.
  const key = JSON.stringify(event);
  useEffect(() => {
    trackEvent(JSON.parse(key) as ViewEvent);
  }, [key]);
  return null;
}
