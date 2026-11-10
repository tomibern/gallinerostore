# Gallinero Store — Discovery y MVP

Nov 9, 2026 · actualizado Nov 10, 2026 · @Tomas

Gallinero Store va a tener un catálogo web responsive (celular y computadora) de indumentaria de fútbol, centrado en River Plate, donde cada consulta termina en WhatsApp o Instagram. No hay carrito, pagos online ni cuentas de clientes; el único usuario es el admin, que carga el catálogo y ve métricas de visitas y consultas por producto. Tanto la tienda como el panel admin se usan completos en celular y en computadora.

## Contexto del negocio

Es un emprendimiento de una sola persona que hoy vende solo por Instagram. Publica historias y posteos con prendas, los interesados escriben por DM y el dueño decide caso por caso si vende desde su stock o le hace un encargue al proveedor.

- **Marca:** Gallinero Store (ya tiene nombre y logo).
- **Foco:** indumentaria de River Plate. Hay un stock básico de River (unos 20 productos) y el resto se trae por encargue, producto por producto, incluidos artículos particulares que pida un cliente. Calidad: «productos de la mejor calidad importada».
- **Tipos de prenda:** camisetas, shorts, buzos, camperas, pantalones y otros. Versiones: retro, tela jugador (player) y tela hincha. No ofrece personalización con nombre, número ni estampados.
- **Cobro:** transferencia o efectivo, coordinados en el chat. No hay medios de pago online.
- **Entrega:** envío a todo el país por Correo Argentino o una empresa similar, gestionado por el dueño; entrega en persona si el comprador es de La Plata.
- **Escala:** emprendimiento mínimo. El ecommerce queda como posible evolución si el catálogo funciona.

### Actores

| Actor | Qué hace | ¿Usa la web? |
|---|---|---|
| Visitante / cliente | Llega desde Instagram, navega el catálogo y consulta por un producto | Sí, sin cuenta |
| Admin (dueño) | Carga y organiza el catálogo, responde consultas en WhatsApp/Instagram, mira métricas | Sí, con login |
| Proveedor | Provee los artículos por encargue | No, relación externa y manual |

## Problema y objetivos

Hoy el catálogo vive disperso en historias que duran 24 horas y en posteos difíciles de recorrer. El cliente no puede ver fácilmente qué hay, en qué talle ni qué se puede encargar. El dueño responde las mismas preguntas una y otra vez y no sabe qué productos generan más interés.

| Objetivo | Cómo lo medimos |
|---|---|
| Mostrar todo el catálogo en un solo lugar, ordenado y siempre disponible | Cantidad de productos publicados; link en la bio de Instagram |
| Que el cliente llegue a la consulta con el producto y el talle ya elegidos | % de consultas que llegan con el mensaje prearmado |
| Que el dueño sepa qué interesa | Visitas y consultas por producto, en el panel del admin |
| Que mantenerlo sea fácil y barato | Cargar un producto en menos de 3 minutos, desde el celular o la computadora; costo de unos pocos USD por mes |

El MVP se considera exitoso si el dueño lo usa como canal principal para mostrar productos (link en bio e historias) y las consultas por WhatsApp/Instagram llegan identificando el producto.

## Flujo de consulta

La web no cambia cómo se cierra la venta: solo ordena cómo llega el cliente a la conversación.

### Hoy

- El dueño publica una historia o un posteo con una prenda.
- El interesado escribe por DM, muchas veces sin decir producto ni talle exactos.
- El dueño pregunta talle, revisa su stock y responde precio y disponibilidad.
- Si no hay stock, ofrece encargarlo y junta pedidos para el proveedor.
- Se acuerda pago (transferencia o efectivo) y entrega: envío por correo a todo el país o en persona en La Plata.

### Con el catálogo

- El interesado entra desde el link en la bio, una historia o un link compartido.
- Navega por sección (**En stock** o **Por encargue**) y filtra por tipo de prenda o talle.
- Abre el detalle: fotos, descripción, talles y precio.
- Elige talle y toca **Consultar por WhatsApp** o **Consultar por Instagram**.
- Se abre el chat con un mensaje prearmado, por ejemplo: «Hola! Me interesa la Camiseta River titular 2026, talle M (en stock). [link]». La web registra la consulta.
- Desde acá sigue igual que hoy: el dueño confirma disponibilidad, encargue, pago y entrega a mano.

**Limitación de Instagram:** WhatsApp permite abrir el chat con el texto ya escrito (wa.me/<número>?text=...). Instagram no: el link ig.me/m/<usuario> abre el DM vacío. En Instagram la web copia el mensaje al portapapeles y avisa «pegalo en el chat».

## Modelo de dominio

La entidad central es el **Producto**. Cada producto pertenece a una categoría, tiene una disponibilidad (stock o encargue), sus talles, fotos y los eventos que genera (visitas y consultas).

### Entidades

| Entidad | Qué representa | Relación |
|---|---|---|
| Producto | Un artículo publicado en el catálogo | Pertenece a 1 categoría y 1 equipo; tiene N talles y N imágenes |
| Categoría | Tipo de prenda: camiseta, short, buzo, campera, pantalón, accesorio | Tiene N productos |
| Equipo | Club o selección (River por defecto; otros para encargues) | Tiene N productos |
| Talle | Talle de un producto y si está disponible | Pertenece a 1 producto |
| Imagen | Foto del producto, con orden (la primera es la portada) | Pertenece a 1 producto |
| Evento | Visita al detalle o clic en consultar (WhatsApp/Instagram) | Pertenece a 1 producto |
| Configuración | Datos de la tienda: WhatsApp +54 9 2920 342004 (link wa.me/5492920342004), Instagram @gallinerostore14, textos de «Cómo comprar» | Única |
| Admin | El dueño, único usuario con login | — |

### Atributos del producto

| Atributo | Tipo | Obligatorio | Notas |
|---|---|---|---|
| Nombre | Texto | Sí | Ej.: «Camiseta River titular 2026» |
| Slug | Texto | Sí | Generado del nombre, para la URL |
| Descripción | Texto largo | No | Material, detalles, calce |
| Categoría | Lista | Sí | Ver entidades |
| Equipo | Lista | Sí | River por defecto |
| Disponibilidad | Stock / Encargue | Sí | Define la sección donde aparece |
| Talles | Lista de talles + disponible sí/no | Sí | Talles estándar de S a XXL. En encargue: talles que se pueden pedir |
| Precio | Número (ARS) | Sí | Lo carga el admin y lo puede editar cuando quiera |
| Temporada | Texto | No | Ej.: 2025/26 |
| Versión | Retro / Tela jugador (player) / Tela hincha | No | Filtro en el listado |
| Demora de encargue | Texto | No | Opcional; el dueño la define en el chat |
| Imágenes | 1 a 6 fotos | Sí (mínimo 1) | La primera es portada |
| Destacado | Sí/No | — | Aparece en la home |
| Visible | Sí/No | — | Ocultar sin borrar |
| Orden | Número | — | Orden manual dentro de su sección |
| Historia de la camiseta | Hitos + cifras + dato curioso | No | Títulos ganados, partidos históricos y anécdotas. Si está vacía, la sección no aparece en el detalle |
| Fecha de alta y de edición | Fecha | Automático | Para «novedades» |

## Reglas de negocio

- **Dos secciones excluyentes.** Cada producto está en **En stock** o en **Por encargue**, nunca en las dos.
- **Stock = disponible ya.** Los talles sin stock se muestran tachados. Si no queda ningún talle, el producto sigue visible con la etiqueta «Agotado / Sin stock» y el botón pasa a «Consultar disponibilidad»; no se promete que se pueda encargar.
- **Encargue = a pedido.** Cada encargue es por producto puntual y no está garantizado. Demora y condiciones se acuerdan en el chat; la web muestra el aviso «Demora y condiciones a confirmar por chat». Para confirmar un encargue se pide una seña del 50%, que se coordina en el chat.
- **Sin stock numérico en el MVP.** Se registra disponible sí/no por talle, no cantidades. Es lo más simple de mantener.
- **Precio siempre visible.** Cada producto tiene un precio en ARS que el admin carga y puede editar en cualquier momento.
- **La consulta no es un pedido.** Tocar «Consultar» solo abre el chat y registra el evento. No se reserva stock ni se crea un pedido.
- **Mensaje prearmado.** Incluye nombre del producto, talle elegido (si hay), disponibilidad y link al producto.
- **Pago y entrega fuera de la web.** Transferencia o efectivo. Envío a todo el país por Correo Argentino o similar, o entrega en persona en La Plata. Todo se coordina en el chat. La web solo lo informa en «Cómo comprar».
- **Pedidos especiales.** Un botón general «¿Buscás algo que no está? Consultanos» abre el chat sin producto, para encargues de otros equipos o artículos particulares.
- **Solo el admin edita.** El catálogo es público y de solo lectura.

## Alcance del MVP

El MVP tiene dos partes: el catálogo público y el panel del admin. Prioridad: **Debe** = sin esto no se lanza; **Debería** = entra si hay tiempo; **Podría** = después del lanzamiento.

**Celular y computadora:** el catálogo público y el panel admin tienen todas sus funciones en los dos dispositivos. No hay una versión «principal» y otra recortada: cambia el diseño según la pantalla, no lo que se puede hacer.

### Catálogo público

| Funcionalidad | Prioridad |
|---|---|
| Home con logo, destacados y accesos a En stock / Por encargue | Debe |
| Carrusel automático de fotos (hasta 4) en los bloques estáticos de la home, como «LBDT 14» | Debe |
| Listado por sección con foto, nombre, precio y etiqueta de disponibilidad | Debe |
| Filtros por tipo de prenda, versión (retro, jugador, hincha) y talle | Debe |
| Detalle con galería de fotos, descripción, selector de talle y demora de encargue | Debe |
| Sección «Historia de la camiseta» en el detalle, opcional por producto | Debe |
| Botones «Consultar por WhatsApp» e «Instagram» con mensaje prearmado | Debe |
| Página «Cómo comprar»: pagos, envíos a todo el país, entrega en La Plata, encargues, preguntas frecuentes | Debe |
| Botón de consulta general para pedidos especiales | Debe |
| Vista previa al compartir un link (Open Graph: foto + nombre) | Debe |
| Buscador por texto | Debería |
| Orden por novedades o precio | Debería |
| Lista de consulta: elegir varios productos y mandarlos en un solo mensaje | Podría |

### Panel del admin

| Funcionalidad | Prioridad |
|---|---|
| Login seguro (un único usuario) | Debe |
| Alta, edición, ocultar y borrar productos | Debe |
| Cargar la historia de la camiseta: hitos (año, título, anécdota), cifras y dato curioso | Debe |
| Subir fotos desde el celular (cámara o galería) o la computadora (arrastrar y soltar), con procesamiento automático | Debe |
| Marcar talles disponibles y mover un producto entre stock y encargue | Debe |
| Marcar destacados | Debe |
| Panel de métricas por producto | Debe |
| Editar configuración: WhatsApp, Instagram, textos de «Cómo comprar» | Debería |
| Cambiar las fotos de los carruseles de la home | Debería |
| Ordenar productos manualmente | Debería |
| Duplicar un producto (para variantes parecidas) | Debería |
| Gestionar categorías y equipos desde el panel | Podría |

### Fuera del MVP

- Carrito, checkout y pagos online (Mercado Pago u otros).
- Cotización y seguimiento de envíos dentro de la web (los envíos existen, pero se coordinan en el chat).
- Cuentas de clientes, favoritos o historial.
- Gestión de pedidos, encargues al proveedor o inventario con cantidades.
- Sincronización automática con Instagram.

Estos puntos forman la base de un posible ecommerce futuro. El modelo de datos se diseña para poder sumarlos sin rehacer todo.

## Métricas

La web registra sus propios eventos en la base de datos, sin cookies ni datos personales. Así el dueño ve visitas y consultas por producto sin depender de herramientas externas.

| Evento | Cuándo se registra | Datos |
|---|---|---|
| product_view | Se abre el detalle de un producto | Producto, fecha, origen (utm_source), dispositivo |
| contact_click | Clic en Consultar | Producto, canal (WhatsApp/Instagram), talle, fecha, origen |
| general_contact_click | Clic en la consulta general | Canal, página, fecha |
| page_view | Visita a home o listados | Página, fecha, origen |

**Lo que ve el admin:**

- Visitas totales y consultas totales por día, semana o mes.
- Ranking de productos por visitas y por consultas.
- Tasa de consulta por producto (consultas / visitas).
- Consultas por canal: WhatsApp vs. Instagram.
- Origen del tráfico: bio, historias, links compartidos (con links etiquetados, por ejemplo ?utm_source=historia).

**Límite:** la web mide interés, no ventas. Las ventas se cierran en el chat. Más adelante se puede sumar un botón «Marcar como vendido» en el admin para estimar la conversión.

Opcional: sumar una analítica gratuita y respetuosa de la privacidad (por ejemplo Vercel Web Analytics o Umami) para datos generales de tráfico.

## Requisitos no funcionales

| Requisito | Criterio |
|---|---|
| Responsive | La tienda y el panel admin funcionan completos en celular y en computadora, con diseño adaptable desde 360 px hasta pantallas anchas. Tienda: en celular, grilla de 2 columnas y botones de consulta fijos abajo; en computadora, grilla de 3 o 4 columnas, filtros en una barra lateral y galería grande. Admin: en celular, formularios a una columna, botones grandes y fotos desde la cámara; en computadora, tabla de productos con más columnas, edición rápida y fotos con arrastrar y soltar. |
| Navegador de Instagram | Tiene que funcionar bien dentro del navegador interno de Instagram (links, copiar al portapapeles, abrir WhatsApp). |
| Velocidad | Listados y detalle cargan en menos de 2 s en 4G. Imágenes en WebP, redimensionadas y con carga diferida. |
| Costo | Frontend, base de datos y fotos en planes gratuitos; la API entre 0 y 5 USD por mes según el hosting; el dominio, unos pocos USD al año. |
| Admin simple | Todo el panel se usa cómodo desde el celular y desde la computadora, sin conocimientos técnicos. |
| SEO básico | Títulos y descripciones por producto, URLs legibles, sitemap. |
| Compartible | Cada producto tiene su URL con vista previa (foto y nombre) en WhatsApp e Instagram. |
| Seguridad | Solo el admin escribe; login con contraseña fuerte o link mágico; HTTPS. |
| Accesibilidad | Contraste suficiente, textos alternativos en fotos, botones grandes. |
| Identidad visual | Usa el logo propio de Gallinero Store (escudo circular rojo, blanco y negro). La paleta sale del logo y del feedback del dueño (10/11): una gama de rojos con blanco; el negro deja de usarse como color de base. |

### Dirección visual

El dueño quiere vistas llamativas y muy integradas con la identidad de River, con fotos de jugadores y del club. La propuesta es que la web se sienta de la tribuna, no una tienda genérica, sin que los productos pierdan protagonismo.

- **Color:** una gama de rojos en lugar del negro. Bordó (#6E1219) de base para textos, bordes y fondos oscuros; rojo vivo y chillón (#E3262F) en el nombre de la tienda, los títulos y los botones de consulta; blanco y rosados claros de fondo. La banda roja diagonal como recurso gráfico: separadores, fondos de sección, etiquetas.
- **Tipografía:** títulos condensados y en mayúsculas, estilo camiseta o bandera; texto de lectura simple.
- **Home:** portada a pantalla completa con una foto del estadio o la tribuna, el logo y el nombre sobre una caja roja (como en el boceto del dueño), accesos grandes a «En stock» y «Por encargue», destacados, y un bloque «LBDT 14» sobre la hinchada.
- **Carruseles:** en los bloques estáticos, como «LBDT 14», un carrusel de hasta 4 fotos que pasan solas (cada 4 segundos) y que también se pueden elegir a mano.
- **Recursos de hinchada:** el 14, banderas, trapos, papelitos, texturas de tribuna.
- **Productos:** fotos sobre fondo limpio y del mismo tamaño, para que el catálogo se vea ordenado aunque la estética sea intensa.
- **Historia de la camiseta:** en el detalle del producto, una sección opcional y en tono divertido: figuritas de álbum con año y título que se dan vuelta para contar la anécdota, algunas cifras y un «¿Sabías que…?».
- **Fotos de jugadores:** ver el riesgo en «Riesgos y mitigaciones». Alternativas sin ese riesgo: fotos propias de hinchas con los productos, fotos de tribuna o del estadio sacadas por el dueño, ilustraciones o bancos de imágenes con licencia comercial.

## Propuesta técnica preliminar

Recomendación: un frontend web (Next.js o Astro) con Supabase como backend (base de datos, login y fotos), publicado en Cloudflare Pages o Netlify en sus planes gratuitos. La decisión final está en «Decisiones técnicas» y reemplaza lo que diga esta sección. Los límites y costos de esta sección son aproximados y hay que verificarlos en cada proveedor.

| Opción | Costo mensual aprox. | A favor | En contra |
|---|---|---|---|
| **A. Next.js/Astro + Supabase en Cloudflare Pages o Netlify** (recomendada) | 0 USD + dominio | Control total, métricas propias, base lista para un ecommerce futuro | Hay que desarrollar el panel del admin |
| B. Igual que A, pero en Vercel | 0 USD en Hobby; unos 20 USD en Pro | Muy buena integración con Next.js | El plan gratuito de Vercel no admite uso comercial |
| C. Plataforma de tiendas armada (Tiendanube, Empretienda, etc.) | Abono mensual | Sin desarrollo | Costo fijo, menos control, pensada para checkout |
| D. Sitio estático + CMS headless (Sanity, Decap) | 0 USD | Panel de carga ya hecho | Las métricas necesitan otro servicio aparte |

### Piezas de la opción A

- **Base de datos:** Postgres en Supabase con tablas products, product_sizes, product_images, categories, teams, events y settings.
- **Login:** Supabase Auth con un solo usuario admin; políticas de seguridad por fila (RLS) para que el público solo pueda leer.
- **Fotos:** Supabase Storage; se comprimen en el navegador antes de subirlas para ahorrar espacio.
- **Eventos:** inserción anónima solo en la tabla events, con límite de frecuencia básico.
- **Dominio:** por ejemplo gallinerostore.com.ar (NIC Argentina) o .com.

**A tener en cuenta:** el plan gratuito de Supabase pausa los proyectos sin actividad por una semana. Con visitas reales no debería pasar, pero conviene un ping periódico automático.

## Decisiones de catálogo

Decisiones tomadas: **producto = modelo + versión** y **variante = talle**. Cada producto es **de stock o de encargue**, y en los de stock cada talle está disponible o sin stock. Hay **un solo precio por producto**. Las categorías son un árbol de dos niveles como máximo, y lo demás se filtra con atributos y etiquetas.

### 1. Qué es un producto y qué es una variante

| Opción | Ejemplo | A favor | En contra |
|---|---|---|---|
| **A. Producto = modelo + versión; variante = talle** (recomendada) | «Camiseta River titular 2026 — Tela jugador» con talles S a XXL | Cada versión tiene su precio y sus fotos; el admin carga algo simple; el mensaje a WhatsApp es claro | Las versiones del mismo modelo son productos separados |
| B. Producto = modelo; variante = versión × talle | «Camiseta River titular 2026» con 3 versiones × 5 talles = 15 variantes | Una sola ficha por modelo | Precio y fotos por variante; el admin se complica mucho para 20 productos |

Con la opción A se pueden vincular las versiones de un mismo modelo («También en tela hincha») con un campo opcional grupo_modelo. Prioridad: Podría.

### 2. Disponibilidad (decidido)

El dueño no garantiza que un talle sin stock se pueda encargar: lo decide en el momento, por chat. Por eso la web no promete encargues de talles agotados.

| Tipo de producto | Talles | Qué muestra la web | Botón |
|---|---|---|---|
| **De stock** | Cada talle: disponible o sin stock | Talles disponibles normales, sin stock tachados. Si no queda ninguno: etiqueta «Sin stock» y el producto sigue visible | «Consultar»; si el talle o el producto están sin stock, «Consultar disponibilidad» |
| **De encargue** | Talles que se pueden pedir | Aviso «A pedido: demora y condiciones a confirmar por chat» | «Consultar encargue» |

- Un producto de stock aparece en **En stock** (con o sin talles disponibles). Uno de encargue aparece en **Por encargue**.
- Si el dueño se queda sin stock y decide traer más, cambia el tipo del producto o vuelve a marcar los talles como disponibles.
- El mensaje a WhatsApp siempre dice el caso: «talle M (en stock)», «talle XL (sin stock, consulto disponibilidad)» o «(por encargue)».

### 3. Categorías y anidación

Recomendación: un árbol corto, de dos niveles como máximo, solo para el tipo de prenda. El equipo, la versión, la temporada y el tipo de camiseta no van en el árbol: son filtros. Un árbol profundo (River → Camisetas → 2026 → Titular) obliga a recorrer muchos niveles en el celular y duplica caminos.

| Nivel 1 | Nivel 2 (opcional) |
|---|---|
| Camisetas | — |
| Abrigos | Buzos, camperas |
| Pantalones | Shorts, pantalones largos |
| Accesorios | Gorras, bufandas, medias (si los hubiera) |

La navegación queda así: sección (En stock / Por encargue) → categoría → filtros (versión, talle, equipo, etiquetas).

### 4. Atributos y etiquetas

| Dato | Tipo | Valores | Uso |
|---|---|---|---|
| Equipo | Entidad propia | River (por defecto) y los que se sumen por encargue | Filtro; por defecto se muestra River |
| Versión | Lista cerrada | Retro, Tela jugador, Tela hincha | Filtro y etiqueta en la tarjeta |
| Temporada | Texto | 2025/26, 1986, etc. | Se muestra en la ficha |
| Etiquetas | Lista abierta, varias por producto | Titular, Alternativa, Tercera, Arquero, Entrenamiento, Pre-match | Filtros secundarios y colecciones de la home |

### 5. Talles

- Talles de prenda: S, M, L, XL, XXL, en ese orden.
- Talle único para accesorios.
- Los talles salen de una tabla propia con su orden, así se pueden sumar talles de niños después sin tocar código.
- Guía de talles por categoría (tabla de medidas). Prioridad: Debería.

### 6. Código, estados y precio

- **Código corto** por producto (por ejemplo GS-014), generado automáticamente. Va en el mensaje de WhatsApp para que el dueño identifique el producto al instante.
- **Estados del producto:** Borrador → Publicado ↔ Oculto → Archivado. Archivar en lugar de borrar: así se conservan las métricas históricas.
- **Precio:** uno por producto, en pesos y sin decimales. Opcional: un «precio anterior» tachado para ofertas (Podría). El precio no varía por talle: un único precio por producto.

## Modelo de datos (borrador)

El modelo refleja las decisiones de catálogo y es genérico para poder reutilizarlo (ver «Sistema reutilizable»). Son 13 tablas en Postgres, definidas con SQLAlchemy y migradas con Alembic; los nombres van en inglés porque es lo habitual en el código.

| Tabla | Campos principales | Notas |
|---|---|---|
| products | id, code, name, slug, description, category_id, collection_id, version_id, season, sale_mode, price, compare_at_price, status, featured, sort_order, model_group, created_at, updated_at | sale_mode: stock / on_order. status: draft / published / hidden / archived. price en la moneda configurada, sin decimales |
| product_sizes | product_id, size_id, in_stock | En productos de stock: disponible sí/no. En los de encargue: talles que se pueden pedir |
| sizes | id, label, sort_order, size_group | S…XXL en el grupo «prenda»; «Único» en «accesorio» |
| categories | id, name, slug, parent_id, sort_order, size_group | parent_id vacío = nivel 1. Máximo 2 niveles, validado en la app |
| collections | id, name, slug, is_default, sort_order | Dimensión configurable: en Gallinero se llama «Equipo» y River es la opción por defecto. Con un solo equipo cargado, el filtro de la tienda y el campo del admin se ocultan solos; al cargar un segundo equipo aparecen, sin cambiar código ni datos |
| versions | id, name, slug, sort_order | Retro, Tela jugador, Tela hincha. Se puede desactivar por configuración |
| tags / product_tags | id, name, slug / product_id, tag_id | Relación de muchos a muchos: titular, alternativa, arquero, etc. |
| product_images | id, product_id, path_full, path_thumb, alt, width, height, sort_order | La primera por sort_order es la portada |
| product_story_items | id, product_id, kind, year, title, body, sort_order | kind: milestone (figurita) / stat (cifra) / fun_fact (¿Sabías que…?). Sin filas, la sección no se muestra. Se apaga con features.productStory |
| home_slides | id, block, path_full, alt, sort_order | Fotos de los carruseles de la home (block: por ejemplo lbdt). Máximo 4 por bloque, validado en la API |
| events | id, type, product_id, channel, size_id, source, device, session_id, created_at | Sin datos personales. session_id es anónimo y se usa para no contar visitas repetidas |
| settings | contact_channels, how_to_buy_md, faq_md, on_order_notice, message_templates | Una sola fila; lo editable desde el admin. Lo técnico va en config/store.toml |

**Valores calculados (no se guardan):** la etiqueta «Sin stock» (producto de stock sin talles disponibles) sale de product_sizes. Una vista catalog_products lo devuelve ya calculado para el catálogo público.

**Permisos:** solo la API accede a la base. Los endpoints públicos solo leen productos publicados y su información relacionada, y solo pueden insertar en events. Los endpoints del admin exigen sesión iniciada.

## Decisiones técnicas

Decisión: **backend en Python con FastAPI, donde vive toda la lógica de negocio**, y frontend en Next.js con TypeScript que solo muestra datos y llama a la API. Postgres sigue siendo la base de datos. Los límites y precios de los planes de hosting hay que verificarlos al crear las cuentas.

### Arquitectura

- **Frontend (Next.js, en Netlify):** catálogo público y panel admin. No tiene lógica de negocio ni acceso a la base; todo pasa por la API.
- **API (FastAPI, Python):** productos, talles, categorías, fotos, login del admin, eventos, métricas y configuración. Es el único que habla con la base y con el almacenamiento de fotos.
- **Base de datos (Postgres):** en Supabase o Neon, usado solo como Postgres administrado.
- **Fotos:** almacenamiento compatible con S3 (Supabase Storage o Cloudflare R2); la API sube y procesa las imágenes.
- **Actualización de datos:** el catálogo se renderiza en el servidor en cada visita (SSR) con datos pedidos a la API, sin caché. Lo que el admin guarda se ve al refrescar la página. Sin webhooks ni regeneración de páginas.

Como cada visita consulta la API, la API tiene que responder rápido: consultas con índices, respuestas chicas y un endpoint pensado para el listado. En producción necesita un hosting que no se duerma (ver «Arranque en frío»).

### Backend (Python)

| Capa | Elección | Por qué |
|---|---|---|
| Lenguaje | Python 3.12+ con type hints | Muy demandado; tipado chequeado con mypy o Pyright |
| Framework | FastAPI | El framework de APIs en Python más pedido hoy; asíncrono, rápido y con documentación OpenAPI automática |
| Validación | Pydantic v2 | Esquemas de entrada y salida; integrado con FastAPI |
| ORM | SQLAlchemy 2.0 (async) | Estándar de la industria en Python |
| Migraciones | Alembic | Migraciones versionadas en el repo: clave para actualizar los forks |
| Login del admin | Propio en la API: contraseña con Argon2 y token JWT en cookie httpOnly | Sin depender de un proveedor; igual en todos los forks |
| Imágenes | Pillow: la API redimensiona a 400 px y 1600 px y convierte a WebP al subir | La lógica queda en el backend, no en el navegador |
| Almacenamiento | boto3 contra una API compatible con S3 (Supabase Storage o Cloudflare R2) | Se cambia de proveedor con configuración |
| Configuración | pydantic-settings (variables de entorno + store_config) | Cada fork define lo suyo sin tocar código |
| Límite de frecuencia | slowapi en los endpoints públicos (eventos) | Evita spam en las métricas |
| Tests | pytest + httpx, con una base Postgres de prueba | Permiten actualizar forks con confianza |
| Calidad | Ruff (lint y formato) + mypy, con pre-commit | Estándar actual en Python |
| Dependencias | uv | El gestor de paquetes de Python más rápido y con más adopción hoy |
| Contenedor | Docker; docker compose para desarrollo local (API + Postgres) | Mismo entorno en todas las máquinas y en el hosting |

Organización por módulos de dominio: catalog (productos, talles, categorías, versiones, colecciones), media (fotos), auth, events, metrics y settings. Cada uno tiene su router, sus esquemas, su servicio con la lógica y su repositorio de datos. Los routers no tienen lógica: todo está en los servicios.

### Frontend (TypeScript)

| Capa | Elección | Por qué |
|---|---|---|
| Framework | Next.js (App Router) + TypeScript | Renderizado en el servidor en cada visita (SSR): datos siempre al día y buen SEO; admin interactivo |
| Estilos | Tailwind CSS + tokens de diseño en variables CSS | Diseño a medida y responsive; cambiar de marca es cambiar tokens |
| Componentes | shadcn/ui para el admin; componentes propios para la tienda | Admin prolijo sin diseñarlo desde cero |
| Cliente de la API | Generado desde el OpenAPI de FastAPI (openapi-typescript u Orval) | Tipos del front sincronizados con el back, sin escribirlos a mano |
| Datos en el admin | TanStack Query | Caché, reintentos y estados de carga |
| Formularios | React Hook Form + Zod | Validación inmediata en pantalla; la validación definitiva la hace la API |
| Gráficos | Recharts | Panel de métricas |
| Tests | Vitest + Playwright, tienda y admin en celular y escritorio | De punta a punta contra la API |

### Entorno de desarrollo local

Todo el desarrollo (fases 2 a 4) corre en la computadora, sin cuentas ni servicios en la nube. Los servicios de producción se crean recién en la fase de deploy. Como la API habla con Postgres y con S3 por configuración, pasar a producción es cambiar variables de entorno, no código.

| Pieza | En local | En producción |
|---|---|---|
| Base de datos | Postgres en Docker | Supabase o Neon |
| API | FastAPI con uvicorn --reload | Cloud Run, Railway o Fly.io |
| Frontend | next dev | Netlify |
| Fotos | MinIO en Docker (compatible con S3) | Cloudflare R2 o Supabase Storage |
| Migraciones | Alembic contra el Postgres local | Alembic en el pipeline de deploy |
| Datos | Seed con productos y fotos de prueba | Carga real desde el admin |
| Configuración | .env.local | Variables de entorno del hosting |

- docker compose up levanta Postgres y MinIO; make dev levanta todo, incluidos la API y el frontend.
- Para probar en el celular: abrir la IP local de la computadora desde la misma red wifi.
- El código va a GitHub desde el primer día (es control de versiones, no hosting).

### Infraestructura de producción (fase de deploy)

| Tema | Decisión | Costo aprox. (verificar) |
|---|---|---|
| Frontend | Netlify (plan gratuito, permite uso comercial) | 0 USD |
| API | Google Cloud Run (escala a cero y tiene cuota gratuita) o Railway / Fly.io | 0 a 5 USD por mes |
| Base de datos | Postgres en Supabase o Neon, plan gratuito | 0 USD |
| Fotos | Cloudflare R2 o Supabase Storage, plan gratuito | 0 USD |
| CI/CD | GitHub Actions: lint, tests, migraciones con Alembic y deploy de los dos servicios | 0 USD |
| Backups | Job semanal en GitHub Actions con pg_dump; también evita que el proyecto gratuito se pause | 0 USD |
| Dominio | A nombre del dueño. gallinerostore.com.ar para la web y api.gallinerostore.com.ar para la API | Pago anual del dueño |

**Arranque en frío:** con SSR, si la API escala a cero, el primer visitante después de un rato sin uso espera unos segundos. En producción conviene una instancia mínima siempre encendida (Railway o Fly.io, o Cloud Run con mínimo 1 instancia), por unos pocos USD por mes (verificar). Se decide en la fase de deploy.

**Repositorio:** monorepo con apps/web (Next.js), apps/api (FastAPI) y packages/api-client (cliente generado).

## Sistema reutilizable

Objetivo: que Gallinero Store sea el primer cliente de un sistema de catálogo que se pueda forkear y adaptar a negocios parecidos (otros vendedores de ropa por Instagram, otros clubes, zapatillas). Esto se decide ahora porque cambia cómo se escribe el código desde el primer día. Agregarlo después implica reescribir.

### Principio: separar el núcleo de lo que cambia en cada cliente

| Capa | Qué contiene | Dónde vive | ¿Cambia por cliente? |
|---|---|---|---|
| Núcleo | Catálogo, admin, métricas, eventos, login, modelo de datos, migraciones | apps/api, apps/web | No. Solo se actualiza desde el repo base |
| Configuración | Nombre, moneda, idioma, canales de contacto, plantillas de mensaje, funciones activadas | config/store.toml + .env | Sí |
| Marca y tema | Logo, colores (tokens), tipografías, imágenes, metadatos y Open Graph | brand/ | Sí |
| Contenido | Productos, categorías, talles, versiones, textos de «Cómo comprar» | Base de datos (se carga desde el admin) | Sí, sin tocar código |
| Personalizaciones | Secciones especiales de la home o componentes propios del cliente | custom/ con puntos de extensión definidos | Solo si hace falta |

Regla de oro: **en el núcleo no aparece nada de River, camisetas ni Gallinero.** Todo lo específico va en configuración, marca o contenido.

### Qué implica en el diseño del sistema

- **Dominio genérico:** el «equipo» pasa a ser una dimensión configurable (Equipo, Marca, Colección), con su etiqueta definida en la configuración y la opción de desactivarla. Las versiones (retro, jugador, hincha) son una tabla editable, no un valor fijo en el código. Los talles, las categorías y las etiquetas ya son datos.
- **Funciones activables:** por ejemplo features.teams, features.versions, features.onOrder, features.instagram, features.metrics, features.productStory. Un cliente que solo vende stock apaga los encargues.
- **Canales de contacto como módulos:** WhatsApp e Instagram hoy; se pueden sumar otros. Las plantillas de mensaje son configurables.
- **Textos fuera de los componentes:** un diccionario de textos (es-AR por defecto), así cada cliente cambia el tono sin tocar componentes y se puede sumar otro idioma.
- **Moneda y formato** desde la configuración (ARS por defecto).
- **Tema por tokens:** la estética River de Gallinero es un tema (brand/gallinero), no el diseño del núcleo. El núcleo trae un tema neutro.
- **Migraciones versionadas e incrementales:** nunca se edita una migración ya publicada; así cada fork puede actualizar su base sin perder datos.
- **Seed por cliente:** un script carga categorías, talles y configuración iniciales.

### Forks: cómo crear y mantener clientes

| Tema | Decisión |
|---|---|
| Repo base | Repositorio privado catalogo-base (nombre a definir) marcado como template en GitHub. Gallinero es el primer fork |
| Crear un cliente | Fork o template → make setup (pide nombre, colores, contacto, crea .env, corre migraciones y seed, crea el admin) → deploy. Objetivo: tienda nueva en menos de un día |
| Actualizar un cliente | Cada fork tiene el repo base como remoto upstream; se trae cada versión con merge. Como el cliente solo toca brand/, custom/ y la configuración, los conflictos son mínimos |
| Versionado | Versiones semánticas del repo base (v1.2.0) con CHANGELOG y notas de migración |
| Seguridad al actualizar | Los tests de Playwright corren en el fork antes del deploy |
| Documentación | README de instalación, guía para crear un cliente nuevo y guía de personalización |

**Evolución posible:** con 3 o 4 clientes, mantener forks se vuelve pesado. El paso siguiente es un monorepo con el núcleo como paquete (@marca/catalog-core) y una app chica por cliente, o una plataforma multi-tienda (SaaS) con store_id en cada tabla. Hoy no hace falta, pero la separación por capas deja ese camino abierto.

### Infraestructura y negocio por cliente

| Tema | Opciones | Nota |
|---|---|---|
| Cuentas de hosting y base | Cada cliente con sus cuentas, o todos en las tuyas | El plan gratuito de Supabase permite pocos proyectos activos por cuenta (verificar): con muchos clientes en tu cuenta hace falta un plan pago. Que cada cliente tenga su cuenta mantiene el costo en cero y la propiedad clara |
| Dominio | Siempre a nombre del cliente | Como en Gallinero |
| Licencia del código | Repo privado y licencia propietaria: el cliente usa el sistema pero no puede revenderlo | Definirlo por escrito en cada contrato |
| Modelo de cobro | Pago único de implementación + abono mensual de mantenimiento y actualizaciones | A definir; el abono justifica mantener los forks al día |
| Marca del sistema | Nombre propio del producto, separado de Gallinero Store | A definir |
| Contenido de terceros | Cada cliente es responsable de sus fotos y marcas | Dejarlo en el contrato, sobre todo por el riesgo de imágenes de jugadores |

## Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación |
|---|---|---|
| El catálogo queda desactualizado (stock o precios viejos) | Alto: consultas frustradas | Admin muy rápido desde el celular o la computadora; aviso «disponibilidad sujeta a confirmación» |
| Marcas registradas: escudo de River y marcas deportivas | Medio: reclamos o bajas de contenido | No usar el escudo oficial en la identidad de la tienda; describir los productos con claridad (original o réplica); consultar si hace falta |
| El dueño no adopta la herramienta | Alto | Diseñar el admin con él; carga inicial asistida; empezar con pocos productos |
| Problemas en el navegador interno de Instagram | Medio | Probar en iOS y Android dentro de Instagram antes de lanzar |
| Límites o cambios en los planes gratuitos | Bajo/medio | Fotos comprimidas; monitorear uso; arquitectura migrable |
| Spam en los eventos que inflan métricas | Bajo | Límite de frecuencia y filtro básico de bots |
| Inflación: precios que cambian seguido | Medio | Editar el precio en segundos desde el celular o la computadora; más adelante, edición masiva de precios |
| Fotos de jugadores e imágenes oficiales del club en una web que vende | Alto: derechos de imagen de los jugadores y derechos de autor de las fotos (club, agencias, fotógrafos); puede dar lugar a reclamos o bajas | Priorizar fotos propias, de hinchas o de tribuna, e ilustraciones. Si se usan fotos de jugadores, que sea con licencia comercial y como decisión explícita del dueño |

## Plan de trabajo

Siete fases en orden; cada una se cierra cuando cumple su criterio de salida. Las duraciones se estiman después de las respuestas del dueño.

| Fase | Entregable | Criterio de salida |
|---|---|---|
| 0. Discovery | Este documento + respuestas del dueño | Preguntas abiertas respondidas; alcance del MVP aprobado |
| 1. Diseño | Wireframes para celular y escritorio de home, listado, detalle, «Cómo comprar» y admin; dirección de arte con identidad River y paleta a partir del logo. Publicados (tienda y admin, celular y escritorio): [claude.ai/artifact/Fp24ciJ6yDajEhyz7Sk7Pb](https://claude.ai/artifact/Fp24ciJ6yDajEhyz7Sk7Pb) | Dueño aprueba las pantallas. Aprobado por el dueño el 10/11 (tienda y admin). |
| 2. Base técnica | Monorepo, API en FastAPI con modelo de datos y migraciones, frontend Next.js y Docker Compose con Postgres y MinIO, todo en local | make dev levanta todo en local; migraciones y seed corren sin errores |
| 3. Catálogo público | Home, listados, filtros, detalle, botones de consulta | Recorrido completo en local con datos de prueba, en celular (misma wifi) y escritorio |
| 4. Admin y métricas | Login, ABM de productos, fotos, panel de métricas | El dueño carga y edita un producto solo, desde el celular y desde la computadora |
| 5. Deploy a producción | Cuentas de hosting, base y fotos; dominio; CI/CD; backups; decisión sobre el arranque en frío | Sitio funcionando en el dominio, probado dentro de Instagram en iOS y Android |
| 6. Lanzamiento | Carga inicial del catálogo, link en bio, historia de lanzamiento | Al menos 20 productos publicados y primeras consultas registradas |

**Después del lanzamiento:** revisar métricas a las 2 y 4 semanas, juntar feedback del dueño y priorizar los «Debería» y «Podría».

## Preguntas abiertas para el dueño

Hay que responderlas antes de cerrar el diseño; varias cambian el modelo de datos.

**Respuestas de la primera charla (9/11/2026).** Las ocho imprescindibles están respondidas, más otras ocho de la segunda charla; en las listas de abajo quedan marcadas las respondidas y siguen abiertas las demás.

| Pregunta | Respuesta del dueño |
|---|---|
| Productos en stock y por encargue | Unos 20 productos en stock. El encargue se maneja por producto puntual |
| Originales o réplicas | «Productos de la mejor calidad importada» (textual) |
| Precios | Cada producto tiene precio; lo carga el admin y lo puede modificar |
| Talles | Estándar, de S a XXL |
| Demora y condiciones del encargue | Las define en el momento de la consulta |
| Canal de consultas | WhatsApp e Instagram, los dos |
| Fotos | Propias del stock; las carga él desde el panel admin |
| Entrega | Envío a todo el país por Correo Argentino o una empresa similar, que gestiona él. Entrega en persona si el comprador es de La Plata |
| Versiones | Retro, tela jugador (player) y tela hincha |
| Personalización | No ofrece nombre, número ni estampados personalizados |
| Producto agotado | Se sigue mostrando, con la etiqueta «Agotado» o «Sin stock» |
| Historias destacadas de Instagram | Dos grupos: stock (entrega inmediata) y encargue (catálogo de lo que se puede traer) |
| Contacto | WhatsApp +54 9 2920 342004 · Instagram @gallinerostore14 |
| Significado del 14 | Referencia a la hinchada de River |
| Dominio | Lo paga el dueño y queda a su nombre |
| Diseño | Vistas llamativas, muy integradas con la identidad de River, con fotos de jugadores y similares |
| Otros equipos (10/11) | Por ahora solo River, pero no tiene que ser limitante: más adelante puede sumar otros equipos. El modelo mantiene «Equipo» y la tienda se adapta sola |
| Seña de encargues (10/11) | Seña del 50% para confirmar un encargue; se coordina en el chat |
| Aprobación del diseño (10/11) | El dueño aprueba los wireframes de la tienda y del admin. Se cierra la fase 1 |
| Feedback de los wireframes (10/11) | Cambiar el negro por una gama de rojos, con rojos más chillones en el nombre de la tienda. Carrusel de hasta 4 fotos en los bloques estáticos como «LBDT 14». Los productos pueden tener, opcional, una historia de la camiseta (títulos ganados, etc.) contada de forma divertida |

**Para entender cómo vende hoy**

- ☐ ¿Qué productos le consultan más? ¿Qué se vende más rápido?
- ☒ ¿Cómo organiza hoy las historias destacadas de Instagram? (base para las categorías)
- ☐ ¿Cuántas consultas recibe por semana y cuántas terminan en venta, aproximadamente?
- ☐ ¿Qué le lleva más tiempo hoy al responder consultas?
- ☐ ¿Cómo decide si hace un encargue: por cantidad de pedidos, por fecha fija o caso por caso?

**Producto y catálogo**

- ☒ ¿Cuántos productos hay hoy en stock y cuántos querría mostrar por encargue?
- ☒ ¿Los productos son originales, réplicas o ambos? ¿Cómo quiere comunicarlo?
- ☒ ¿Qué versiones maneja: hincha, jugador, retro, entrenamiento?
- ☒ ¿Qué talles maneja? ¿Hay talles de niños o mujer?
- ☒ ¿Ofrece personalización con nombre y número? ¿Con costo extra?
- ☒ ¿Muestra otros equipos además de River, o solo los trae a pedido? Por ahora solo River; puede sumar otros más adelante.
- ☒ ¿Cuando algo se agota, prefiere mostrarlo como «Agotado» u ocultarlo?

**Precios y encargues**

- ☒ ¿Quiere mostrar precios o prefiere «Consultar precio»? ¿Cada cuánto cambian?
- ☒ ¿Cuál es la demora típica de un encargue? ¿Varía por producto?
- ☒ ¿Pide seña para los encargues? ¿Cuánto? Sí, del 50%.
- ☒ ¿Hay un mínimo de pedidos para hacer un encargue al proveedor?

**Contacto, pago y entrega**

- ☒ ¿Qué número de WhatsApp y qué usuario de Instagram se usan?
- ☒ ¿Prefiere recibir consultas por WhatsApp, por Instagram o por los dos?
- ☒ ¿Dónde y cómo entrega? ¿Punto de encuentro, zona, horarios?
- ☐ ¿Qué preguntas le hacen más seguido? (base para la sección de preguntas frecuentes)

**Contenido y operación**

- ☒ ¿Las fotos son propias o del proveedor? ¿Tiene fotos de buena calidad del stock actual?
- ☒ ¿Quién va a cargar los productos y desde qué dispositivo?
- ☐ ¿Tiene el logo en alta calidad (SVG o PNG con fondo transparente)?
- ☒ ¿Qué dominio le gustaría? ¿Quién lo paga y a nombre de quién queda?
- ☐ ¿Qué tendría que pasar en los primeros 2 meses para que diga que la web le sirvió?

**Marca y logo**

- ☐ ¿Tiene el archivo original del logo (vector: SVG, AI o PDF)? ¿Quién lo diseñó?
- ☐ ¿Hay versiones alternativas: horizontal, monocromática o un ícono reducido para favicon?
- ☐ ¿Cuáles son los colores exactos (rojo, negro, blanco) y la tipografía del logo?
- ☒ ¿Qué significa el 14? (para una sección «Sobre nosotros»)
- ☐ El monograma con las letras entrelazadas recuerda al monograma clásico del club. ¿Es un diseño propio? ¿Consideró el riesgo marcario?

## Glosario

| Término | Significado en este proyecto |
|---|---|
| Stock | Producto que el dueño tiene físicamente y puede entregar ya |
| Encargue | Producto que se pide al proveedor después de la consulta; tiene demora y se confirma en el chat con una seña del 50% |
| Consulta | Clic en «Consultar» que abre WhatsApp o Instagram con el producto; no es un pedido ni una venta |
| Mensaje prearmado | Texto que la web prepara con producto, talle y link para iniciar la conversación |
| Talle | Medida de la prenda (S, M, L, XL, etc.); en stock se marca si está disponible |
| Versión hincha | Camiseta de calce y tela estándar, la que se vende al público |
| Versión jugador | Camiseta de calce ajustado y tela técnica, como la que usan en la cancha |
| Retro | Reedición de una camiseta histórica |
| Titular / alternativa | Camiseta principal del club / camiseta de visitante o tercera |
| Temporada | Año o ciclo de la camiseta (ej.: 2025/26) |
| Destacado | Producto que el admin elige mostrar en la home |
| Admin | El dueño, único usuario con acceso al panel |
| MVP | Primera versión mínima que se lanza para validar el catálogo |
