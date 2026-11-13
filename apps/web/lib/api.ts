// Acceso a la API desde el servidor de Next (SSR) con el cliente generado.
// El navegador nunca llama a la API directo: usa /api/* (ADR 0003).

import { cache } from "react";

import { createApiClient, type ProductListItem, type PublicStore } from "@catalog/api-client";

import { apiInternalUrl } from "./env";

export type { ProductListItem, PublicStore };
export type Section = ProductListItem["section"];
export type Availability = ProductListItem["availability"];

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

/** Productos publicados de una sección, en el orden manual, o null si la API no responde. */
export async function getSectionProducts(section: Section): Promise<ProductListItem[] | null> {
  try {
    const { data } = await api().GET("/products", {
      params: { query: { section } },
      cache: "no-store",
    });
    return data ?? null;
  } catch {
    return null;
  }
}
