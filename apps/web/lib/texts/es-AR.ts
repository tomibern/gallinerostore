// Textos de UI del núcleo en es-AR, neutros: sirven para cualquier tienda.
// Cada cliente puede pisar claves en config/texts.json (sin tocar componentes).
// Los textos vacíos son opcionales: el componente no los muestra.

export const esAR = {
  // Tienda
  "store.tagline": "",
  "store.unavailable": "La tienda no está disponible en este momento. Probá de nuevo en un rato.",

  // Navegación
  "nav.label": "Navegación principal",
  "nav.menuOpen": "Abrir menú",
  "nav.stock": "En stock",
  "nav.onOrder": "Por encargue",
  "nav.howToBuy": "Cómo comprar",

  // Pie
  "footer.label": "Pie de página",
  "footer.links": "Enlaces",

  // Producto
  "product.story.title": "Historia del producto",
} as const satisfies Record<string, string>;

export type TextKey = keyof typeof esAR;
