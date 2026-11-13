import { t, type TextKey } from "@/lib/texts";

// Rutas fijas del núcleo para recorrer la tienda (encabezado y pie).
const NAV: { href: string; label: TextKey }[] = [
  { href: "/stock", label: "nav.stock" },
  { href: "/encargue", label: "nav.onOrder" },
  { href: "/como-comprar", label: "nav.howToBuy" },
];

export function navLinks() {
  return NAV.map(({ href, label }) => ({ href, label: t(label) }));
}
