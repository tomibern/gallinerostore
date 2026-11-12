# Gallinero Store

Catálogo de indumentaria de fútbol donde el visitante elige un producto y talle, y la consulta sigue en WhatsApp o Instagram. Los términos valen para el núcleo genérico; lo específico de Gallinero (River, LBDT 14) es contenido o marca.

## Catálogo

**Producto**:
Un artículo publicado: un modelo en una versión (ej.: «Camiseta River titular 2026 — Tela jugador»), con un solo precio y de 1 a 6 imágenes.
_Evitar_: artículo, ítem, prenda (como entidad)

**Talle**:
La variante de un producto. Pertenece a un grupo de talles ordenado (prenda: S a XXL; accesorio: Único).
_Evitar_: variante, medida

**Modo de venta**:
Si un producto es de **stock** o de **encargue**. Lo elige el admin y no cambia solo: un producto de stock agotado sigue siendo de stock.
_Evitar_: tipo, disponibilidad (para esto)

**Stock**:
Producto que el dueño tiene y entrega ya. Cada talle está disponible o sin stock, sin cantidades.
_Evitar_: inventario, existencias

**Sin stock**:
Talle de un producto de stock que no está disponible. Se muestra tachado y se puede consultar su disponibilidad.

**Agotado**:
Producto de stock sin ningún talle disponible. Se calcula, no se guarda. Mientras está agotado aparece en «Por encargue», avisando que se agotó, y se puede pedir en cualquier talle de su grupo; vuelve a «En stock» en cuanto un talle está disponible.
_Evitar_: sin stock (para el producto entero)

**Encargue**:
Producto que se pide al proveedor después de la consulta. Se puede pedir en cualquier talle de su grupo y nunca tiene stock. No está garantizado; demora y seña del 50% se acuerdan en el chat.
_Evitar_: preventa, pedido, backorder

**Sección**:
Cada una de las dos vistas del catálogo público: «En stock» y «Por encargue». Un producto está en una sola. Se deriva del modo de venta y de si está agotado: un producto de stock agotado aparece en «Por encargue».
_Evitar_: tienda, listado (como entidad)

**Categoría**:
Tipo de prenda, en un árbol de 2 niveles como máximo (ej.: Abrigos → Buzos).

**Colección**:
Dimensión configurable que en Gallinero se llama «Equipo» (River por defecto). En otro cliente puede ser «Marca».
_Evitar_: equipo, club (en el núcleo)

**Versión**:
Calidad o reedición del modelo: Retro, Tela jugador, Tela hincha. Cada cliente define las suyas.
_Evitar_: calidad, tipo de tela

**Etiqueta**:
Atributo libre, varios por producto (Titular, Alternativa, Arquero…), usado como filtro secundario.

**Precio**:
Monto único por producto, en la moneda de la tienda. No varía por talle.

**Destacado**:
Producto que el admin elige mostrar en la home.

**Estado**:
Ciclo de vida del producto: borrador → publicado ↔ oculto → archivado. Solo un borrador se puede borrar; un producto que se publicó alguna vez se archiva.
_Evitar_: visible/invisible

**Código**:
Identificador corto y permanente del producto (ej.: GS-014). Va en el mensaje prearmado y es lo que identifica al producto en su link, así un link compartido sigue funcionando aunque cambie el nombre.
_Evitar_: SKU

**Historia del producto**:
Sección opcional del detalle con hitos, cifras y un dato curioso. En Gallinero se muestra como «historia de la camiseta», con los hitos como figuritas.
_Evitar_: historia de la camiseta (en el núcleo)

## Consulta y métricas

**Consulta**:
Clic en «Consultar» que abre WhatsApp o Instagram con el mensaje prearmado y registra un evento. No es un pedido ni una venta.
_Evitar_: pedido, orden, compra, lead

**Consulta general**:
Consulta sin producto, para pedidos especiales.

**Mensaje prearmado**:
Texto con producto, código, talle, disponibilidad (en stock, sin stock, por encargue o agotado por encargue) y link que la web prepara para abrir la conversación. En WhatsApp viaja dentro del link; en Instagram se muestra para que la persona lo copie si quiere.

**Canal de contacto**:
Destino de una consulta: WhatsApp o Instagram, configurable por cliente.

**Evento**:
Registro anónimo de interés: visita a una página, visita al detalle de un producto, consulta o consulta general.
_Evitar_: tracking, analytics (para esto)

## Sistema

**Admin**:
El dueño de la tienda, único usuario con login.
_Evitar_: usuario, vendedor

**Núcleo**:
Código compartido por todos los clientes. No conoce ningún cliente concreto.

**Cliente**:
Un negocio que usa el sistema mediante un fork del repo base. Gallinero Store es el primero.
_Evitar_: tenant, tienda (para el fork)

**Marca**:
Logo, tokens de color, tipografías e imágenes de un cliente. La estética River es la marca de Gallinero, no el núcleo.
_Evitar_: tema (como sinónimo)
