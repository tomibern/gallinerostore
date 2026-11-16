// Acceso a la API desde el navegador con el cliente generado. Nunca va directo a
// la API: pide a /api/*, que Next reenvía (ADR 0003). Sin imports del servidor.

import { createApiClient, type ProductList } from "@catalog/api-client";

import type { Section } from "./api";
import type { Listing } from "./listing";

const api = createApiClient("/api");

/** Una página del listado de una sección con los filtros y el orden de la URL. */
export async function getListingPage(
  section: Section,
  listing: Listing,
  { offset, limit }: { offset: number; limit: number },
): Promise<ProductList> {
  const { data, error } = await api.GET("/products", {
    params: { query: { section, ...listing, offset, limit } },
    cache: "no-store",
  });
  if (!data) throw new Error(`GET /products falló: ${JSON.stringify(error)}`);
  return data;
}
