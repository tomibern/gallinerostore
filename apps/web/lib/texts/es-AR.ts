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

  // Secciones
  "section.stock.title": "En stock",
  "section.stock.description": "Lo que tenemos para entregar ya.",
  "section.onOrder.title": "Por encargue",
  "section.onOrder.description": "Lo pedimos al proveedor después de tu consulta.",
  "section.empty": "Todavía no hay productos en esta sección.",
  "section.unavailable": "No pudimos cargar los productos. Probá de nuevo en un rato.",

  // Disponibilidad de un producto
  "availability.in_stock": "En stock",
  "availability.on_order": "Por encargue",
  "availability.sold_out_on_order": "Se agotó · disponible por encargue",
  "availability.sold_out": "Agotado",

  // Producto
  "product.story.title": "Historia del producto",
} as const satisfies Record<string, string>;

export type TextKey = keyof typeof esAR;
