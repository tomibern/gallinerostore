// t() de la tienda: diccionario es-AR del núcleo con los reemplazos del
// cliente (config/texts.json, copiado por scripts/sync-brand.mjs) encima.

import { esAR } from "./es-AR";
import overrides from "./overrides.generated.json";
import { createPrefixedTexts, createTranslator } from "./translator";

export type { TextKey } from "./es-AR";
export type { TextVars } from "./translator";

export const t = createTranslator(esAR, overrides);

const blockTexts = createPrefixedTexts("home.blocks.", overrides);

/**
 * Título o texto de un bloque de la home. El núcleo no conoce las claves de los
 * bloques (las declara la tienda), así que solo salen de config/texts.json
 * (`home.blocks.<clave>.title` y `.text`); si faltan, vacío.
 */
export function homeBlockText(block: string, field: "title" | "text"): string {
  return blockTexts(`${block}.${field}`);
}
