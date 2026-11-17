"use client";

import { useEffect } from "react";

import { type EventFields, recordEvent, startVisit } from "@/lib/events";

type ViewEvent = Extract<EventFields, { type: "page_view" | "product_view" }>;

// Registra la visita al cargar la página en el navegador (no en el SSR: el prefetch y
// la mayoría de los bots no corren efectos). No dibuja nada. En desarrollo, el Strict
// Mode de React la manda dos veces; en producción, una.
export function RecordView({ event }: { event: ViewEvent }) {
  // Por valor: otro producto (o página) es otra visita; filtrar o cargar más, no.
  const key = JSON.stringify(event);
  useEffect(() => {
    recordEvent(JSON.parse(key) as ViewEvent);
  }, [key]);
  return null;
}

// Fija el origen de la visita (utm_source) con la URL por la que se entró, en cualquier
// página de la tienda. Va en el layout. No dibuja nada.
export function RecordVisit() {
  useEffect(startVisit, []);
  return null;
}
