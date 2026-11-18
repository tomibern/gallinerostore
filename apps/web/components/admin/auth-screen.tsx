import { DiagonalBand } from "@/components/store/diagonal-band";
import { StoreLogo } from "@/components/store/store-logo";

// Pantallas sin sesión (login, recuperar y elegir contraseña): la misma tarjeta en
// celular y escritorio, centrada.
export function AuthScreen({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-dvh flex-col bg-panel">
      <DiagonalBand className="h-3 shrink-0" />
      <main className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center gap-6 px-5 py-6">
        <div className="flex flex-col items-center gap-3 text-center">
          <StoreLogo className="size-28" />
          <h1 className="font-display text-3xl font-bold text-primary uppercase">{title}</h1>
          <p className="text-sm text-muted">{subtitle}</p>
        </div>
        {children}
      </main>
    </div>
  );
}

/** La tarjeta del formulario. */
export const AUTH_CARD =
  "flex flex-col gap-4 bg-surface px-5 py-6 shadow-[0_8px_24px_color-mix(in_srgb,var(--color-accent)_12%,transparent)]";
