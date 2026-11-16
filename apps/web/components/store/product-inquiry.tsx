"use client";

import { useState } from "react";

import type { ProductDetail } from "@/lib/api";

type Props = {
  sizes: ProductDetail["sizes"];
  labels: {
    legend: string;
    choose: string;
    outOfStock: string;
    // La línea de estado de cada talle, por etiqueta («Talle M · en stock»).
    status: Record<string, string>;
  };
};

// Consulta del detalle: por ahora, el selector de talle y su línea de estado; el
// talle elegido vive acá para que los botones de Consultar se sumen al lado. El estado de
// cada talle ya viene calculado de la API; acá solo se elige. Con talle único,
// viene elegido. Los sin stock se ven tachados, pero se pueden elegir.
export function ProductInquiry({ sizes, labels }: Props) {
  const [chosen, setChosen] = useState<string | null>(sizes.length === 1 ? sizes[0].label : null);
  const size = sizes.find((s) => s.label === chosen);

  if (sizes.length === 0) return null;

  return (
    <div className="flex flex-col gap-3">
      <fieldset className="flex flex-col gap-2">
        <legend className="font-display mb-2 text-sm font-semibold tracking-wide uppercase">
          {labels.legend}
        </legend>
        <div className="flex flex-wrap gap-2">
          {sizes.map(({ label, status }) => (
            <label key={label} data-size={label} className="cursor-pointer">
              <input
                type="radio"
                name="size"
                value={label}
                checked={chosen === label}
                onChange={() => setChosen(label)}
                className="peer sr-only"
              />
              <span
                className={`flex h-11 min-w-11 items-center justify-center rounded-sm border px-3 text-sm font-medium transition-colors peer-checked:border-primary peer-checked:bg-primary peer-checked:text-primary-contrast peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-primary ${
                  status === "out_of_stock"
                    ? "border-border bg-surface text-muted line-through"
                    : "border-border bg-surface text-text"
                }`}
              >
                {label}
                {status === "out_of_stock" && (
                  <span className="sr-only"> ({labels.outOfStock})</span>
                )}
              </span>
            </label>
          ))}
        </div>
      </fieldset>
      <p
        aria-live="polite"
        data-testid="size-status"
        data-status={size?.status ?? ""}
        className={`text-sm ${size?.status === "out_of_stock" ? "text-error" : "text-muted"}`}
      >
        {size ? labels.status[size.label] : labels.choose}
      </p>
    </div>
  );
}
