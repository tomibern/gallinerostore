import Image from "next/image";

import brand from "@/lib/brand.generated.json";

// Logo de la marca (brand/<marca>/public/logo.*). Sin logo, no dibuja nada.
// Va siempre junto al nombre de la tienda, así que es decorativo (alt vacío).
// El tamaño en pantalla lo da className; se pide al doble para pantallas densas.
export function StoreLogo({ className }: { className: string }) {
  if (!brand.logo) return null;

  return (
    <Image
      src={brand.logo}
      alt=""
      width={96}
      height={96}
      className={`shrink-0 rounded-full bg-surface ${className}`}
    />
  );
}
