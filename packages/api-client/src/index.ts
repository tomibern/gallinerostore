// Cliente tipado de la API. Los tipos salen de schema.d.ts, que se genera desde
// el OpenAPI de FastAPI con `make gen-client`: no editar schema.d.ts a mano.
import createClient from "openapi-fetch";

import type { components, paths } from "./schema";

export type ApiClient = ReturnType<typeof createApiClient>;

export function createApiClient(baseUrl: string) {
  return createClient<paths>({ baseUrl });
}

export type Schemas = components["schemas"];
export type ProductListItem = Schemas["ProductListItem"];
export type PublicStore = Schemas["PublicStore"];
export type ProductList = Schemas["ProductList"];
export type ProductFacets = Schemas["ProductFacets"];
export type FacetValue = Schemas["FacetValue"];
export type CategoryFacetValue = Schemas["CategoryFacetValue"];
export type HomeBlock = Schemas["HomeBlock"];
export type HomeSlideOut = Schemas["HomeSlideOut"];
export type ProductDetail = Schemas["ProductDetail"];
export type ProductSizeOut = Schemas["ProductSizeOut"];
export type SizeStatus = Schemas["SizeStatus"];
export type Inquiry = Schemas["Inquiry"];
export type Channel = Schemas["Channel"];
export type FaqItem = Schemas["FaqItem"];
