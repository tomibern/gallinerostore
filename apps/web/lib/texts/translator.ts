// Función t() propia y tipada: los textos del núcleo con los reemplazos del
// cliente encima. Sin librería de i18n.

export type Dictionary = Readonly<Record<string, string>>;

export type TextVars = Readonly<Record<string, string | number>>;

/** Reemplazos válidos: solo claves que existen en el núcleo y con texto. */
function validOverrides(core: Dictionary, overrides: unknown): Record<string, string> {
  if (typeof overrides !== "object" || overrides === null) return {};
  return Object.fromEntries(
    Object.entries(overrides).filter(
      ([key, value]) => Object.hasOwn(core, key) && typeof value === "string",
    ),
  );
}

export function createTranslator<D extends Dictionary>(core: D, overrides: unknown) {
  const texts: Dictionary = { ...core, ...validOverrides(core, overrides) };

  return function t(key: keyof D & string, vars?: TextVars): string {
    const text = texts[key];
    if (!vars) return text;
    return text.replace(/\{(\w+)\}/g, (match, name: string) =>
      Object.hasOwn(vars, name) ? String(vars[name]) : match,
    );
  };
}

/**
 * Textos que el núcleo no puede declarar porque dependen de la configuración
 * del cliente (por ejemplo, los bloques de la home: `home.blocks.<clave>.title`).
 * Solo salen de los reemplazos del cliente, bajo un prefijo; si falta, vacío.
 */
export function createPrefixedTexts(prefix: string, overrides: unknown) {
  const texts: Record<string, unknown> =
    typeof overrides === "object" && overrides !== null ? { ...overrides } : {};

  return function text(key: string): string {
    const value = texts[`${prefix}${key}`];
    return typeof value === "string" ? value : "";
  };
}
