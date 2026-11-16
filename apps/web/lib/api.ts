// Acceso a la API desde el servidor de Next (SSR) con el cliente generado.
// El navegador nunca llama a la API directo: usa /api/* (ADR 0003).

import { cache } from "react";

import {
  createApiClient,
  type CategoryFacetValue,
  type Channel,
  type Inquiry,
  type FacetValue,
  type HomeBlock,
  type HomeSlideOut,
  type ProductDetail,
  type ProductFacets,
  type ProductList,
  type ProductListItem,
  type PublicStore,
} from "@catalog/api-client";

import { apiInternalUrl } from "./env";
import type { Listing } from "./listing";

export type {
  CategoryFacetValue,
  Channel,
  Inquiry,
  FacetValue,
  HomeBlock,
  HomeSlideOut,
  ProductDetail,
  ProductFacets,
  ProductList,
  ProductListItem,
  PublicStore,
};
export type Section = ProductListItem["section"];
export type Availability = ProductListItem["availability"];
export type SizeStatus = ProductDetail["sizes"][number]["status"];

/** Un producto, que no existe (o no está publicado), o la API que no responde. */
export type ProductResult =
  { status: "ok"; product: ProductDetail } | { status: "not_found" } | { status: "error" };

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
 * Los primeros `limit` productos del listado de una sección con los filtros y el
 * orden de la URL, el total y los valores de filtro disponibles; null si la API
 * no responde.
 */
export async function getSectionListing(
  section: Section,
  listing: Listing,
  limit: number,
): Promise<ProductList | null> {
  try {
    const { data } = await api().GET("/products", {
      params: { query: { section, ...listing, limit } },
      cache: "no-store",
    });
    return data ?? null;
  } catch {
    return null;
  }
}

// Destacados que muestra la home.
export const MAX_FEATURED = 8;

/** Los primeros destacados publicados, en su orden manual; null si la API no responde. */
export async function getFeatured(): Promise<ProductListItem[] | null> {
  try {
    const { data } = await api().GET("/products", {
      params: { query: { featured: true, limit: MAX_FEATURED } },
      cache: "no-store",
    });
    return data ? data.items : null;
  } catch {
    return null;
  }
}

/**
 * Detalle de un producto publicado por su código. Distingue «no existe» (404) de
 * «la API no responde»: un corte no tiene que marcar los productos como inexistentes.
 * Un pedido por render (la página y sus metadatos lo comparten).
 */
export const getProduct = cache(async (code: string): Promise<ProductResult> => {
  try {
    const { data, response } = await api().GET("/products/{code}", {
      params: { path: { code } },
      cache: "no-store",
    });
    if (data) return { status: "ok", product: data };
    return response.status === 404 ? { status: "not_found" } : { status: "error" };
  } catch {
    return { status: "error" };
  }
});
