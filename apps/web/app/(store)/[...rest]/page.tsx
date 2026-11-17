import { notFound } from "next/navigation";

// No es código muerto: Next usa la metadata de not-found.tsx en el navegador solo
// si notFound() sale de generateMetadata. Llamarlo solo desde la página deja el
// título y la descripción del layout después de renderizar en el cliente (#55).
export function generateMetadata(): never {
  notFound();
}

// Cualquier URL sin ruta cae acá y muestra la 404 de la tienda (con encabezado
// y pie). Las rutas fijas y las rewrites de /api y /media se resuelven antes.
export default function UnknownPage() {
  notFound();
}
