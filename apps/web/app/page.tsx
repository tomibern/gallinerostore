import { getStore } from "@/lib/api";

import { HealthStatus } from "./health-status";

// Página de verificación del esqueleto: el nombre llega por SSR desde la
// configuración de la tienda y la salud se pide desde el navegador vía /api.
// Si la API no responde, la página igual se muestra y lo dice.
export const dynamic = "force-dynamic";

export default async function Home() {
  const store = await getStore();

  return (
    <main className="mx-auto flex min-h-dvh max-w-xl flex-col items-center justify-center gap-6 px-4 text-center">
      <h1 className="font-display text-4xl font-bold uppercase tracking-tight text-primary sm:text-5xl">
        {store?.name ?? "Sin conexión con la API"}
      </h1>
      <p className="rounded-full border border-border bg-surface px-4 py-2 text-sm">
        {store && (
          <span className="text-muted">
            {store.currency} · {store.locale} ·{" "}
          </span>
        )}
        <HealthStatus />
      </p>
    </main>
  );
}
