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
