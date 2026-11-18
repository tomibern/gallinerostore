// Textos de UI del núcleo en es-AR, neutros: sirven para cualquier tienda.
// Cada cliente puede pisar claves en config/texts.json (sin tocar componentes).
// Los textos vacíos son opcionales: el componente no los muestra.

export const esAR = {
  // Tienda
  "store.tagline": "",
  "store.unavailable": "La tienda no está disponible en este momento. Probá de nuevo en un rato.",

  // Metadatos: título de la pestaña, descripción y vista previa al compartir.
  // En la plantilla, %s es el título de cada página.
  "meta.titleTemplate": "%s · {store}",
  "meta.home.description": "Catálogo de {store}. Elegí lo que te gusta y consultanos por chat.",
  // El precio va primero: WhatsApp muestra una o dos líneas de la descripción.
  "meta.product.description": "{price} · {availability}",
  "meta.product.descriptionWithText": "{price} · {availability} · {text}",

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
  "listing.search.label": "Buscar en esta sección",
  "listing.search.placeholder": "Buscar por nombre o código",
  "listing.search.submit": "Buscar",
  "listing.search.clear": "Borrar búsqueda",
  "listing.search.empty": "No encontramos productos para «{q}».",
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
  "product.story.hint": "Tocá cada tarjeta para darla vuelta.",
  "product.story.milestones": "Hitos",
  "product.story.stats": "En números",
  "product.story.funFact": "¿Sabías que…?",
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

  // Panel del admin
  "admin.meta.title": "Panel",
  "admin.panel.label": "Panel",
  "admin.unavailable": "No pudimos conectar con el panel. Revisá tu conexión y probá de nuevo.",
  "admin.retry": "Probar de nuevo",
  "admin.nav.label": "Secciones del panel",
  "admin.nav.products": "Productos",
  "admin.nav.metrics": "Métricas",
  "admin.nav.content": "Contenido y ajustes",
  "admin.nav.contentShort": "Contenido",
  "admin.nav.store": "Ver tienda",
  "admin.nav.logOut": "Cerrar sesión",
  "admin.empty": "Todavía no hay nada acá.",
  "admin.account.title": "Cuenta",
  "admin.account.signedInAs": "Entraste como {email}.",
  "admin.settings.save": "Guardar",
  "admin.settings.saving": "Guardando…",
  "admin.settings.saved": "Guardado. La tienda lo muestra desde la próxima visita.",
  "admin.settings.invalid": "Hay campos para revisar.",
  "admin.settings.error": "No pudimos guardar. Revisá tu conexión y probá de nuevo.",
  "admin.settings.loadError": "No pudimos cargar los ajustes. Revisá tu conexión y probá de nuevo.",
  "admin.contact.title": "Contacto",
  "admin.contact.whatsapp": "WhatsApp",
  "admin.contact.whatsappHint":
    "Con el código del país, como lo pide WhatsApp. Si queda vacío, no se ofrece.",
  "admin.contact.instagram": "Usuario de Instagram",
  "admin.contact.instagramHint": "Sin la @. Si queda vacío, no se ofrece.",
  "admin.contact.error.whatsapp":
    "Tiene que ser un número con el código del país: entre 8 y 15 dígitos.",
  "admin.contact.error.instagram": "Solo letras, números, puntos y guiones bajos, hasta 30.",
  "admin.contact.error.unknownVariable":
    "{variable} no existe en este mensaje. Usá los botones para insertar las que sí.",
  "admin.contact.error.required": "No puede quedar vacío.",
  "admin.contact.error.tooLong": "Es demasiado largo: hasta {max} caracteres.",
  "admin.contact.error.invalid": "Revisá este campo.",
  "admin.messages.title": "Mensajes prearmados",
  "admin.messages.hint":
    "Es lo que se escribe solo en el chat cuando alguien consulta. Las palabras entre llaves se completan con los datos del producto: insertalas con los botones.",
  "admin.messages.case.stock": "Talle disponible",
  "admin.messages.case.out_of_stock": "Talle sin stock",
  "admin.messages.case.on_order": "Encargue",
  "admin.messages.case.sold_out_on_order": "Agotado que pasó a encargue",
  "admin.messages.case.general": "Consulta general",
  "admin.messages.variable.product": "Producto",
  "admin.messages.variable.code": "Código",
  "admin.messages.variable.size": "Talle",
  "admin.messages.variable.link": "Link",
  "admin.messages.insert": "Insertar {variable} en «{template}»",
  "admin.messages.preview": "Vista previa",
  "admin.messages.previewWith": "Con {product} ({code}), talle {size}:",
  "admin.messages.previewGeneral": "Así llega al chat:",
  "admin.messages.previewError": "No pudimos armar la vista previa.",
  "admin.notice.title": "Aviso de encargue",
  "admin.notice.label": "Demora y seña",
  "admin.notice.hint": "Se muestra en los productos por encargue. Si queda vacío, no se muestra.",

  // Login del admin
  "admin.login.title": "Panel de {store}",
  "admin.login.subtitle": "Solo para el administrador",
  "admin.login.email": "Email",
  "admin.login.password": "Contraseña",
  "admin.login.remember": "Mantener la sesión iniciada en este dispositivo",
  "admin.login.submit": "Entrar",
  "admin.login.submitting": "Entrando…",
  "admin.login.invalid": "Email o contraseña incorrectos.",
  "admin.login.tooMany": "Demasiados intentos. Esperá 15 minutos y probá de nuevo.",
  "admin.login.error": "No pudimos conectar. Revisá tu conexión y probá de nuevo.",
} as const satisfies Record<string, string>;

export type TextKey = keyof typeof esAR;
