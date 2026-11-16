import { notFound } from "next/navigation";

// Cualquier URL sin ruta cae acá y muestra la 404 de la tienda (con encabezado
// y pie). Las rutas fijas y las rewrites de /api y /media se resuelven antes.
export default function UnknownPage() {
  notFound();
}
