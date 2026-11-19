// Cliente tipado de la API. Los tipos salen de schema.d.ts, que se genera desde
// el OpenAPI de FastAPI con `make gen-client`: no editar schema.d.ts a mano.
import createClient from "openapi-fetch";

import type { components, paths } from "./schema";

export type ApiClient = ReturnType<typeof createApiClient>;

export function createApiClient(baseUrl: string, headers?: Record<string, string>) {
  return createClient<paths>({ baseUrl, headers });
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
export type Device = Schemas["Device"];
export type Page = Schemas["Page"];
// El cuerpo de POST /events: la unión de los cuatro tipos (el OpenAPI no le da nombre).
export type EventIn =
  | Schemas["PageView"]
  | Schemas["ProductView"]
  | Schemas["ContactClick"]
  | Schemas["GeneralContactClick"];
export type StoryItemOut = Schemas["StoryItemOut"];
export type StoryItemKind = Schemas["StoryItemKind"];
export type AdminOut = Schemas["AdminOut"];
export type LoginIn = Schemas["LoginIn"];
export type MetricsSummary = Schemas["MetricsSummary"];
export type MetricsPeriod = Schemas["Period"];
export type AdminSettings = Schemas["AdminSettings"];
export type AdminSettingsIn = Schemas["AdminSettingsIn"];
export type HowToBuyContent = Schemas["HowToBuyContent"];
export type MessageCase = Schemas["MessageCase"];
export type MessageVariable = Schemas["MessageVariable"];
export type MessagePreview = Schemas["MessagePreview"];
export type ValidationError = Schemas["ValidationError"];
export type PasswordResetIn = Schemas["PasswordResetIn"];
export type PasswordResetConfirmIn = Schemas["PasswordResetConfirmIn"];
export type PasswordChangeIn = Schemas["PasswordChangeIn"];
export type AdminFilter = Schemas["AdminFilter"];
export type AdminProductList = Schemas["AdminProductList"];
export type AdminProductListItem = Schemas["AdminProductListItem"];
