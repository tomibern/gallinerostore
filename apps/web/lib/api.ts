// Acceso a la API desde el servidor de Next (SSR). El navegador usa /api/*.
// En el ticket del catálogo esto se reemplaza por el cliente generado.

import { apiInternalUrl } from "./env";

export type PublicStore = {
  name: string;
  locale: string;
  currency: string;
  price_decimals: number;
  collection_label: string;
};

/** Datos públicos de la tienda, o null si la API no responde. */
export async function getStore(): Promise<PublicStore | null> {
  try {
    const response = await fetch(`${apiInternalUrl()}/store`, { cache: "no-store" });
    return response.ok ? ((await response.json()) as PublicStore) : null;
  } catch {
    return null;
  }
}
