"use client";

import Image from "next/image";
import { useRef } from "react";

import type { ProductDetail } from "@/lib/api";

type Props = {
  images: ProductDetail["images"];
  // pick: un texto por foto, en el mismo orden («Ver foto 1»…).
  labels: { gallery: string; pick: string[] };
};

// Galería del detalle: una fila con scroll-snap (en el celular se desliza con el
// dedo) y, con más de una foto, miniaturas que llevan a cada una. La primera
// foto es la que se ve al cargar: se pide sin demora.
export function ProductGallery({ images, labels }: Props) {
  const track = useRef<HTMLUListElement>(null);

  function show(index: number) {
    const slide = track.current?.children[index] as HTMLElement | undefined;
    track.current?.scrollTo({ left: slide?.offsetLeft ?? 0, behavior: "smooth" });
  }

  if (images.length === 0) return <div className="aspect-square rounded-md bg-surface" />;

  return (
    <section aria-label={labels.gallery} className="flex flex-col gap-3">
      <ul
        ref={track}
        data-testid="gallery"
        className="flex snap-x snap-mandatory overflow-x-auto rounded-md bg-surface [scrollbar-width:none]"
      >
        {images.map((image, index) => (
          <li key={image.full} className="w-full shrink-0 snap-center">
            {/* Las fotos ya llegan redimensionadas y en WebP: sin optimizador de Next. */}
            <Image
              src={image.full}
              alt={image.alt}
              width={image.width}
              height={image.height}
              sizes="(min-width: 768px) 50vw, 100vw"
              unoptimized
              loading={index === 0 ? "eager" : "lazy"}
              fetchPriority={index === 0 ? "high" : "auto"}
              className="aspect-square size-full object-contain"
            />
          </li>
        ))}
      </ul>
      {images.length > 1 && (
        <ul data-testid="gallery-thumbs" className="flex gap-2 overflow-x-auto">
          {images.map((image, index) => (
            <li key={image.thumb} className="shrink-0">
              <button
                type="button"
                aria-label={labels.pick[index]}
                onClick={() => show(index)}
                className="block size-16 cursor-pointer overflow-hidden rounded-sm border border-border md:size-20"
              >
                <Image
                  src={image.thumb}
                  alt=""
                  width={image.width}
                  height={image.height}
                  unoptimized
                  className="size-full object-cover"
                />
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
