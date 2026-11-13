// Acceso a la API desde el servidor de Next (SSR) con el cliente generado.
// El navegador nunca llama a la API directo: usa /api/* (ADR 0003).

import { cache } from "react";

import { createApiClient, type PublicStore } from "@catalog/api-client";

import { apiInternalUrl } from "./env";

export type { PublicStore };

function api() {
  return createApiClient(apiInternalUrl());
}

/** Datos públicos de la tienda, o null si la API no responde. Un pedido por render. */
export const getStore = cache(async (): Promise<PublicStore | null> => {
  try {
    const { data } = await api().GET("/store", { cache: "no-store" });
    return data ?? null;
  } catch {
    return null;
  }
});
