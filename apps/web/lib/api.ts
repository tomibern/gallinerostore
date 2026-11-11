// Acceso a la API desde el servidor de Next (SSR). El navegador usa /api/*.
// En el ticket del catálogo esto se reemplaza por el cliente generado.

const apiInternalUrl = process.env.API_INTERNAL_URL ?? "http://localhost:8000";

export type PublicStore = {
  name: string;
  locale: string;
  currency: string;
  price_decimals: number;
  collection_label: string;
};

export async function getStore(): Promise<PublicStore> {
  const response = await fetch(`${apiInternalUrl}/store`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`La API respondió ${response.status} en /store`);
  }
  return response.json() as Promise<PublicStore>;
}
