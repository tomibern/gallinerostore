"use client";

import { useId, useState } from "react";

type Props = { year: number | null; title: string; body: string | null; tilt: string };

// Una figurita de la historia: año y título al frente, la anécdota atrás. Sigue el
// patrón «disclosure» de WAI-ARIA: un botón con aria-expanded que muestra el dorso
// (aria-controls). El botón cubre la figurita entera, así se da vuelta con clic,
// toque, Enter o Espacio, y su nombre es solo año y título: la anécdota queda
// afuera del botón, en el dorso, que se oculta a los lectores de pantalla mientras
// no se ve. Con movimiento reducido, cambia de cara sin girar.
export function StoryCard({ year, title, body, tilt }: Props) {
  const [flipped, setFlipped] = useState(false);
  const backId = useId();
  const name = year === null ? title : `${year} · ${title}`;

  return (
    <li className={`relative h-44 w-36 shrink-0 perspective-distant md:h-56 md:w-44 ${tilt}`}>
      <div
        className={`relative size-full transition-transform duration-500 transform-3d motion-reduce:transition-none ${flipped ? "rotate-y-180" : ""}`}
      >
        <div
          aria-hidden="true"
          className="absolute inset-0 flex flex-col items-center justify-center gap-2 border-3 border-primary bg-surface p-3 text-center shadow-md backface-hidden"
        >
          <svg
            width="30"
            height="30"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="text-primary"
          >
            <path d="M8 4h8v5a4 4 0 0 1-8 0V4zM8 6H5a3 3 0 0 0 3 4M16 6h3a3 3 0 0 1-3 4M12 13v4M8 20h8M9 17h6" />
          </svg>
          {year !== null && (
            <span className="font-display text-3xl font-bold text-primary">{year}</span>
          )}
          <span className="text-xs font-bold tracking-wide uppercase md:text-sm">{title}</span>
        </div>
        <div
          id={backId}
          aria-hidden={!flipped}
          className="absolute inset-0 overflow-y-auto border-3 border-accent bg-accent p-3 text-sm leading-snug text-on-accent shadow-md rotate-y-180 backface-hidden"
        >
          {body ?? title}
        </div>
      </div>
      <button
        type="button"
        aria-expanded={flipped}
        aria-controls={backId}
        onClick={() => setFlipped((value) => !value)}
        className="absolute inset-0 cursor-pointer focus-visible:outline-3 focus-visible:outline-offset-4 focus-visible:outline-primary"
      >
        <span className="sr-only">{name}</span>
      </button>
    </li>
  );
}
