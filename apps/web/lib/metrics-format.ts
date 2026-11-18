// Cómo se muestran los números de las métricas. Los calcula la API: acá solo se
// formatean (porcentajes, signo del cambio y etiquetas del gráfico).

type ChartPoint = { date: string; hour?: number | null };

export function formatCount(value: number, locale: string): string {
  return new Intl.NumberFormat(locale).format(value);
}

/** Una parte de 0 a 1 como porcentaje («12 %»; con un decimal si es menos de 10 %). */
export function formatShare(share: number, locale: string): string {
  return new Intl.NumberFormat(locale, {
    style: "percent",
    maximumFractionDigits: share > 0 && share < 0.1 ? 1 : 0,
  }).format(share);
}

/** Un cambio relativo con signo («+25 %», «−10 %», «0 %»). */
export function formatChange(change: number, locale: string): string {
  return new Intl.NumberFormat(locale, {
    style: "percent",
    maximumFractionDigits: 0,
    signDisplay: "exceptZero",
  }).format(change);
}

// Las fechas llegan como día de la tienda (AAAA-MM-DD), sin hora: se leen en UTC para
// que la zona del navegador no las corra.
function day(date: string): Date {
  return new Date(`${date}T00:00:00Z`);
}

/** Etiqueta corta de una barra por día: el día de la semana (7 días) o la fecha. */
export function chartLabel(point: ChartPoint, total: number, locale: string): string {
  const options: Intl.DateTimeFormatOptions =
    total <= 7 ? { weekday: "short" } : { day: "numeric", month: "numeric" };
  return new Intl.DateTimeFormat(locale, { ...options, timeZone: "UTC" }).format(day(point.date));
}

/** El día de una barra en largo, para lectores de pantalla («martes, 17 de noviembre»). */
export function chartLongDate(point: ChartPoint, locale: string): string {
  return new Intl.DateTimeFormat(locale, {
    weekday: "long",
    day: "numeric",
    month: "long",
    timeZone: "UTC",
  }).format(day(point.date));
}

/** Cada cuántas barras se escribe la etiqueta, para que no se pisen. */
export function labelEvery(total: number, wide: boolean): number {
  if (total <= 7) return 1;
  if (total <= 24) return wide ? 2 : 4;
  return wide ? 3 : 5;
}
