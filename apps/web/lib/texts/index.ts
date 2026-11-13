// t() de la tienda: diccionario es-AR del núcleo con los reemplazos del
// cliente (config/texts.json, copiado por scripts/sync-brand.mjs) encima.

import { esAR } from "./es-AR";
import overrides from "./overrides.generated.json";
import { createTranslator } from "./translator";

export type { TextKey } from "./es-AR";
export type { TextVars } from "./translator";

export const t = createTranslator(esAR, overrides);
