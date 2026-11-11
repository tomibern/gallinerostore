// Acceso a la API desde el servidor de Next (SSR) con el cliente generado.
// El navegador nunca llama a la API directo: usa /api/* (ADR 0003).

import { createApiClient, type ProductListItem, type PublicStore } from "@catalog/api-client";

import { apiInternalUrl } from "./env";

export type { ProductListItem, PublicStore };

function api() {
  return createApiClient(apiInternalUrl());
}

/** Datos públicos de la tienda, o null si la API no responde. */
export async function getStore(): Promise<PublicStore | null> {
  try {
    const { data } = await api().GET("/store", { cache: "no-store" });
    return data ?? null;
  } catch {
    return null;
  }
}

/** Productos publicados, o null si la API no responde. */
export async function getProducts(): Promise<ProductListItem[] | null> {
  try {
    const { data } = await api().GET("/products", { cache: "no-store" });
    return data ?? null;
  } catch {
    return null;
  }
}
