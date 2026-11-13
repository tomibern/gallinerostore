// Acceso a la API desde el servidor de Next (SSR) con el cliente generado.
// El navegador nunca llama a la API directo: usa /api/* (ADR 0003).

import { cache } from "react";

import {
  createApiClient,
  type CategoryFacetValue,
  type FacetValue,
  type ProductFacets,
  type ProductList,
  type ProductListItem,
  type PublicStore,
} from "@catalog/api-client";

import { apiInternalUrl } from "./env";
import type { Listing } from "./listing";

export type {
  CategoryFacetValue,
  FacetValue,
  ProductFacets,
  ProductList,
  ProductListItem,
  PublicStore,
};
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

/**
 * Listado de una sección con los filtros y el orden de la URL, y los valores de
 * filtro disponibles; null si la API no responde.
 */
export async function getSectionListing(
  section: Section,
  listing: Listing,
): Promise<ProductList | null> {
  try {
    const { data } = await api().GET("/products", {
      params: { query: { section, ...listing } },
      cache: "no-store",
    });
    return data ?? null;
  } catch {
    return null;
  }
}
