// Textos de UI del núcleo en es-AR, neutros: sirven para cualquier tienda.
// Cada cliente puede pisar claves en config/texts.json (sin tocar componentes).
// Los textos vacíos son opcionales: el componente no los muestra.

export const esAR = {
  // Tienda
  "store.tagline": "",
  "store.unavailable": "La tienda no está disponible en este momento. Probá de nuevo en un rato.",

  // Home
  "home.access.label": "Secciones",
  "home.featured.title": "Destacados",
  "home.carousel.label": "Fotos",
  "home.carousel.role": "carrusel",
  "home.carousel.slideRole": "foto",
  "home.carousel.stop": "Detener fotos",
  "home.carousel.start": "Reanudar fotos",
  "home.carousel.picker": "Elegir foto",
  "home.carousel.pick": "Ver foto {n}",
  "home.carousel.slide": "{n} de {total}",

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

  // Filtros y orden del listado
  "listing.filters": "Filtros",
  "listing.filter.category": "Categoría",
  "listing.filter.version": "Versión",
  "listing.filter.tag": "Etiquetas",
  "listing.filter.size": "Talle",
  "listing.clear": "Limpiar filtros",
  "listing.sort": "Ordenar por",
  "listing.sort.manual": "Destacados",
  "listing.sort.newest": "Más nuevos",
  "listing.sort.price_asc": "Menor precio",
  "listing.sort.price_desc": "Mayor precio",
  "listing.count.one": "1 producto",
  "listing.count.other": "{count} productos",
  "listing.empty": "No hay productos con estos filtros.",
  "listing.loadMore": "Ver más",
  "listing.loading": "Cargando más productos…",
  "listing.loadError": "No se pudieron cargar más productos. Probá de nuevo.",
  "listing.shown": "Mostrando {shown} de {total} productos",

  // Disponibilidad de un producto
  "availability.in_stock": "En stock",
  "availability.on_order": "Por encargue",
  "availability.sold_out_on_order": "Se agotó · disponible por encargue",
  "availability.sold_out": "Agotado",

  // Producto
  "product.story.title": "Historia del producto",
  "product.unavailable": "No pudimos cargar el producto. Probá de nuevo en un rato.",
  "product.category": "Categoría",
  "product.version": "Versión",
  "product.season": "Temporada",
  "product.onOrderNotice": "A pedido: demora y condiciones a confirmar por chat",
  "product.gallery.label": "Fotos",
  "product.gallery.pick": "Ver foto {n}",
  "product.size.legend": "Talle",
  "product.size.outOfStock": "sin stock",
  "product.size.choose": "Elegí un talle",
  "product.size.status.in_stock": "Talle {size} · en stock",
  "product.size.status.out_of_stock": "Talle {size} · sin stock, consultá disponibilidad",
  "product.size.status.on_order": "Talle {size} · por encargue",

  // Consulta por WhatsApp o Instagram
  "inquiry.action.idle": "Elegí un talle para consultar",
  "inquiry.action.in_stock": "Consultar",
  "inquiry.action.out_of_stock": "Consultar disponibilidad",
  "inquiry.action.on_order": "Consultar encargue",
  "inquiry.channel.whatsapp": "WhatsApp",
  "inquiry.channel.instagram": "Instagram",
  // El botón completo, en escritorio y para lectores de pantalla.
  "inquiry.channel.long": "{action} por {channel}",
  "inquiry.channel.idle": "Consultar",
  "inquiry.sheet.title": "Consultá por Instagram",
  "inquiry.sheet.text": "Abrí Instagram y mandanos este mensaje. Si querés, copialo antes.",
  "inquiry.sheet.copy": "Copiar mensaje",
  "inquiry.sheet.copied": "Mensaje copiado",
  "inquiry.sheet.copyFailed": "No pudimos copiarlo. Seleccioná el texto y copialo a mano.",
  "inquiry.sheet.open": "Abrir Instagram",
  "inquiry.sheet.close": "Cerrar",

  // Consulta general: algo que no está en el catálogo
  "generalInquiry.title": "¿Buscás algo que no está?",
  "generalInquiry.text": "Consultanos y lo buscamos.",
  "generalInquiry.footer": "¿Buscás algo que no está? Consultanos",

  // Cómo comprar
  "howToBuy.title": "Cómo comprar",
  "howToBuy.description": "Pagos, envíos, entregas y encargues: todo se arregla por chat.",
  "howToBuy.empty": "Todavía no cargamos esta información. Escribinos y te contamos.",
  "howToBuy.faq": "Preguntas frecuentes",
  "howToBuy.questions.title": "¿Te quedó alguna duda?",
  "howToBuy.questions.text": "Escribinos y te respondemos por chat.",

  // Página no encontrada
  "notFound.title": "No encontramos esta página",
  "notFound.text": "Puede que el producto ya no esté publicado o que el link esté mal escrito.",
  "notFound.sections": "Seguí recorriendo",
} as const satisfies Record<string, string>;

export type TextKey = keyof typeof esAR;
