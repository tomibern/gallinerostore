# Gallinero Store

Catálogo de indumentaria de fútbol donde el visitante elige un producto y talle, y la consulta sigue en WhatsApp o Instagram. Los términos valen para el núcleo genérico; lo específico de Gallinero (River, LBDT 14) es contenido o marca.

Entre paréntesis, el nombre en código cuando difiere.

## Catálogo

**Producto** (`product`):
Un artículo publicado: un modelo en una versión (ej.: «Camiseta River titular 2026 — Tela jugador»), con un solo precio y de 1 a 6 imágenes.
_Evitar_: artículo, ítem, prenda (como entidad)

**Talle** (`size`):
La variante de un producto. Viene de una tabla ordenada por grupo (`prenda`: S…XXL; `accesorio`: Único).
_Evitar_: variante, medida

**Modo de venta** (`sale_mode`):
Si un producto es de **stock** (`stock`) o de **encargue** (`on_order`). Define en qué sección aparece; nunca los dos.
_Evitar_: tipo, disponibilidad (para esto)

**Stock**:
Producto que el dueño tiene y entrega ya. Cada talle está disponible o sin stock (`in_stock`), sin cantidades.
_Evitar_: inventario, existencias

**Sin stock**:
Producto de stock sin ningún talle disponible. Se calcula, no se guarda; sigue visible.
_Evitar_: agotado (en código)

**Encargue** (`on_order`):
Producto que se pide al proveedor después de la consulta. No está garantizado; demora y seña del 50% se acuerdan en el chat.
_Evitar_: preventa, pedido, backorder

**Sección**:
Cada una de las dos vistas del catálogo público: «En stock» y «Por encargue», derivadas del modo de venta.
_Evitar_: tienda, listado (como entidad)

**Categoría** (`category`):
Tipo de prenda, en un árbol de 2 niveles como máximo (ej.: Abrigos → Buzos).

**Colección** (`collection`):
Dimensión configurable que en Gallinero se llama «Equipo» (River por defecto). En otro cliente puede ser «Marca».
_Evitar_: equipo, club (en el núcleo)

**Versión** (`version`):
Calidad o reedición del modelo: Retro, Tela jugador, Tela hincha. Tabla editable.
_Evitar_: calidad, tipo de tela

**Etiqueta** (`tag`):
Atributo libre, varios por producto (Titular, Alternativa, Arquero…), usado como filtro secundario.

**Destacado** (`featured`):
Producto que el admin elige mostrar en la home.

**Estado** (`status`):
Ciclo de vida del producto: borrador → publicado ↔ oculto → archivado. Se archiva en lugar de borrar.
_Evitar_: visible/invisible

**Código** (`code`):
Identificador corto del producto (ej.: GS-014) que va en el mensaje prearmado.
_Evitar_: SKU

**Historia de la camiseta** (`product_story_items`):
Sección opcional del detalle con hitos (figuritas), cifras y un dato curioso.

## Consulta y métricas

**Consulta**:
Clic en «Consultar» que abre WhatsApp o Instagram con el mensaje prearmado y registra un evento. No es un pedido ni una venta.
_Evitar_: pedido, orden, compra, lead

**Consulta general**:
Consulta sin producto, para pedidos especiales.

**Mensaje prearmado** (`message_templates`):
Texto con producto, código, talle, modo de venta y link que la web prepara para abrir la conversación.

**Canal de contacto** (`channel`):
Destino de una consulta: WhatsApp o Instagram, configurable por cliente.

**Evento** (`event`):
Registro anónimo de interés: `page_view`, `product_view`, `contact_click`, `general_contact_click`.
_Evitar_: tracking, analytics (para esto)

## Sistema

**Admin**:
El dueño de la tienda, único usuario con login.
_Evitar_: usuario, vendedor

**Núcleo**:
Código compartido por todos los clientes (`apps/`). No conoce ningún cliente concreto.

**Cliente**:
Un negocio que usa el sistema mediante un fork del repo base. Gallinero Store es el primero.
_Evitar_: tenant, tienda (para el fork)

**Marca** (`brand/`):
Logo, tokens de color, tipografías e imágenes de un cliente. La estética River es la marca de Gallinero, no el núcleo.
_Evitar_: tema (como sinónimo)
