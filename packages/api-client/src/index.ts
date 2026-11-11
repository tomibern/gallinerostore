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
