import type { Availability } from "@/lib/api";
import { t } from "@/lib/texts";

// Etiqueta de disponibilidad que calcula la API. Solo cambia el estilo por caso.
const STYLE: Record<Availability, string> = {
  in_stock: "bg-primary text-primary-contrast",
  on_order: "bg-accent text-on-accent",
  sold_out_on_order: "bg-surface text-text border border-border",
  sold_out: "bg-surface text-muted border border-border",
};

export function AvailabilityBadge({
  availability,
  className = "",
}: {
  availability: Availability;
  className?: string;
}) {
  return (
    <span
      data-availability={availability}
      className={`font-display rounded-sm px-1.5 py-0.5 text-[11px] leading-tight font-semibold tracking-wide uppercase md:text-xs ${STYLE[availability]} ${className}`}
    >
      {t(`availability.${availability}`)}
    </span>
  );
}
