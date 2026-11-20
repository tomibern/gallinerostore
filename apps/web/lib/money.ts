// Los precios llegan en la unidad menor de la moneda (ADR 0002). Cuántos
// decimales tiene esa unidad sale de la norma ISO de la moneda; cuántos se
// muestran, de la configuración de la tienda (ARS: sin decimales).

function minorUnitDigits(currency: string): number {
  return (
    new Intl.NumberFormat("en", { style: "currency", currency }).resolvedOptions()
      .maximumFractionDigits ?? 2
  );
}

export function formatPrice(
  minorUnits: number,
  currency: string,
  locale: string,
  displayDecimals: number,
): string {
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
    minimumFractionDigits: displayDecimals,
    maximumFractionDigits: displayDecimals,
  }).format(minorUnits / 10 ** minorUnitDigits(currency));
}

// Los separadores que usa el idioma de la tienda (es-AR: miles con «.», decimales con «,»).
function separators(locale: string): { group: string; decimal: string } {
  const parts = new Intl.NumberFormat(locale, { useGrouping: true }).formatToParts(1000.5);
  return {
    group: parts.find((part) => part.type === "group")?.value ?? ",",
    decimal: parts.find((part) => part.type === "decimal")?.value ?? ".",
  };
}

/**
 * El precio que tipea el admin («45000», «45.000» o «$ 45.000») en la unidad menor de
 * la moneda (ADR 0002), con los decimales que muestra la tienda: si no muestra
 * decimales, no se pueden tipear. Null si no es un precio.
 */
export function parsePrice(
  typed: string,
  currency: string,
  locale: string,
  displayDecimals: number,
): number | null {
  const { group, decimal } = separators(locale);
  // Los espacios (también el duro de Intl) y el símbolo de la moneda no cuentan.
  const text = typed.replace(/[\s ]/g, "").replace(currencySymbol(currency, locale), "");
  const [whole, fraction = "", ...rest] = text.split(decimal);
  if (rest.length > 0 || fraction.length > displayDecimals) return null;
  const grouped = whole.split(group);
  // Los separadores de miles, si hay, van cada tres cifras.
  if (grouped.slice(1).some((chunk) => chunk.length !== 3)) return null;
  const digits = grouped.join("");
  if (!/^\d+$/.test(digits) || !/^\d*$/.test(fraction)) return null;
  const value = Number(`${digits}.${fraction || "0"}`);
  return Math.round(value * 10 ** minorUnitDigits(currency));
}

/** Un precio en la unidad menor como lo tipearía el admin: sin símbolo ni miles. */
export function priceInput(
  minorUnits: number,
  currency: string,
  locale: string,
  displayDecimals: number,
): string {
  return new Intl.NumberFormat(locale, {
    useGrouping: false,
    minimumFractionDigits: displayDecimals,
    maximumFractionDigits: displayDecimals,
  }).format(minorUnits / 10 ** minorUnitDigits(currency));
}

/** El símbolo de la moneda en el idioma de la tienda («$» para ARS en es-AR). */
export function currencySymbol(currency: string, locale: string): string {
  const parts = new Intl.NumberFormat(locale, { style: "currency", currency }).formatToParts(0);
  return parts.find((part) => part.type === "currency")?.value ?? currency;
}
