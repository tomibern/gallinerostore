"use client";

import Image from "next/image";
import { useEffect, useId, useState, useSyncExternalStore, type FocusEvent } from "react";

import type { HomeSlideOut } from "@/lib/api";

// Cada foto se ve 4 s antes de pasar a la siguiente.
const INTERVAL_MS = 4000;

const REDUCED_MOTION = "(prefers-reduced-motion: reduce)";

function subscribeReducedMotion(onChange: () => void) {
  const query = window.matchMedia(REDUCED_MOTION);
  query.addEventListener("change", onChange);
  return () => query.removeEventListener("change", onChange);
}

/** Si la persona pidió reducir el movimiento en su sistema (en el servidor, no). */
function useReducedMotion(): boolean {
  return useSyncExternalStore(
    subscribeReducedMotion,
    () => window.matchMedia(REDUCED_MOTION).matches,
    () => false,
  );
}

type Props = {
  slides: HomeSlideOut[];
  title: string;
  text: string;
  // Textos ya resueltos en el servidor: el diccionario no viaja al navegador.
  labels: {
    region: string;
    role: string;
    slideRole: string;
    stop: string;
    start: string;
    picker: string;
    pick: string[];
    slide: string[];
  };
};

// Carrusel accesible (patrón Carousel del WAI-ARIA APG): las fotos pasan solas,
// se eligen a mano y un botón detiene o reanuda la rotación (WCAG 2.2.2). La
// rotación se frena con el mouse encima y se detiene con el foco del teclado
// adentro (no se reanuda sola). Con «reducir movimiento» arranca detenido.
export function HomeCarousel({ slides, title, text, labels }: Props) {
  const titleId = useId();
  const [index, setIndex] = useState(0);
  // null: nadie tocó el botón; gira salvo que se pida reducir el movimiento.
  const [choice, setPlaying] = useState<boolean | null>(null);
  const reducedMotion = useReducedMotion();
  const playing = choice ?? !reducedMotion;
  const [hovered, setHovered] = useState(false);
  const rotates = slides.length > 1;
  const running = rotates && playing && !hovered;

  // Cada cambio de foto (sola o a mano) reinicia la cuenta.
  useEffect(() => {
    if (!running) return;
    const timer = setTimeout(() => setIndex((i) => (i + 1) % slides.length), INTERVAL_MS);
    return () => clearTimeout(timer);
  }, [running, index, slides.length]);

  function stopOnKeyboardFocus(event: FocusEvent<HTMLElement>) {
    // Un clic también enfoca el botón; solo el foco del teclado detiene la rotación.
    if (event.target.matches(":focus-visible")) setPlaying(false);
  }

  return (
    <section
      aria-roledescription={labels.role}
      aria-labelledby={title ? titleId : undefined}
      aria-label={title ? undefined : labels.region}
      data-testid="home-carousel"
      className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-8 md:px-16 md:py-12"
    >
      {title && (
        <h2
          id={titleId}
          className="font-display text-3xl leading-none font-bold uppercase md:text-5xl"
        >
          {title}
        </h2>
      )}
      {text && <p className="text-muted md:text-lg">{text}</p>}

      <div
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        onFocus={stopOnKeyboardFocus}
        className="flex flex-col gap-3"
      >
        {rotates && (
          // Primer elemento enfocable del carrusel, como pide el APG.
          <div className="order-last flex items-center gap-3">
            <button
              type="button"
              onClick={() => setPlaying(!playing)}
              aria-label={playing ? labels.stop : labels.start}
              data-testid="carousel-rotation"
              className="flex size-11 shrink-0 cursor-pointer items-center justify-center rounded-full border border-border bg-surface"
            >
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="currentColor"
                aria-hidden="true"
              >
                <path d={playing ? "M6 4h4v16H6zM14 4h4v16h-4z" : "M7 4l13 8-13 8z"} />
              </svg>
            </button>
            <div role="group" aria-label={labels.picker} className="flex gap-1">
              {slides.map((slide, i) => (
                <button
                  key={slide.full}
                  type="button"
                  aria-label={labels.pick[i]}
                  aria-disabled={i === index}
                  onClick={() => setIndex(i)}
                  className="group flex size-11 cursor-pointer items-center justify-center aria-disabled:cursor-default"
                >
                  <span className="size-3 rounded-full border-2 border-primary group-aria-disabled:bg-primary" />
                </button>
              ))}
            </div>
          </div>
        )}

        <div
          aria-live={running ? "off" : "polite"}
          aria-atomic="false"
          className="relative aspect-[4/3] overflow-hidden rounded-md bg-surface md:aspect-[16/7]"
        >
          {slides.map((slide, i) => {
            const active = i === index;
            return (
              <div
                key={slide.full}
                role="group"
                aria-roledescription={labels.slideRole}
                aria-label={labels.slide[i]}
                aria-hidden={!active}
                data-index={i}
                data-active={active ? "" : undefined}
                className={`absolute inset-0 motion-safe:transition-opacity motion-safe:duration-700 ${
                  active ? "opacity-100" : "opacity-0"
                }`}
              >
                {/* Ya llegan en WebP de 1600 px desde la API: sin el optimizador de Next. */}
                <Image
                  src={slide.full}
                  alt={slide.alt}
                  fill
                  sizes="(min-width: 1280px) 1152px, 100vw"
                  unoptimized
                  className="object-cover"
                />
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
