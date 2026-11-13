import Image from "next/image";
import Link from "next/link";

import type { ProductListItem, PublicStore } from "@/lib/api";
import { formatPrice } from "@/lib/money";

import { AvailabilityBadge } from "./availability-badge";

// Tarjeta de un producto en el listado: foto, nombre, precio y disponibilidad.
// El link usa el código (en minúsculas): renombrar el producto no lo rompe.
export function ProductCard({ product, store }: { product: ProductListItem; store: PublicStore }) {
  const price = formatPrice(product.price, product.currency, store.locale, store.price_decimals);

  return (
    <li data-code={product.code} className="group">
      <Link
        href={`/p/${product.code.toLowerCase()}`}
        className="flex h-full flex-col overflow-hidden rounded-md border border-border bg-surface"
      >
        <div className="relative aspect-square bg-bg">
          {product.cover && (
            // Las fotos ya llegan redimensionadas y en WebP desde la API: no hace
            // falta el optimizador de Next.
            <Image
              src={product.cover.thumb}
              alt={product.cover.alt}
              width={product.cover.width}
              height={product.cover.height}
              sizes="(min-width: 1024px) 25vw, (min-width: 768px) 33vw, 50vw"
              unoptimized
              className="size-full object-cover transition-transform group-hover:scale-[1.03]"
            />
          )}
          <AvailabilityBadge
            availability={product.availability}
            className="absolute top-2 left-2 max-w-[calc(100%-1rem)]"
          />
        </div>
        <div className="flex flex-1 flex-col gap-1 p-2.5 md:p-3">
          <h2 className="line-clamp-2 text-sm leading-snug font-medium md:text-base">
            {product.name}
          </h2>
          <p className="font-display mt-auto text-lg font-bold text-primary md:text-xl">{price}</p>
        </div>
      </Link>
    </li>
  );
}
