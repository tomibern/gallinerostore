// Banda diagonal: recurso gráfico del núcleo (separadores, bordes de bloque).
// Toma los dos tonos del primario de los tokens de la marca.
export function DiagonalBand({ className = "" }: { className?: string }) {
  return (
    <div
      aria-hidden="true"
      className={`bg-[repeating-linear-gradient(135deg,var(--color-primary)_0_14px,var(--color-primary-strong)_14px_28px)] ${className}`}
    />
  );
}
