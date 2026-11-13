import Link from "next/link";

import { t } from "@/lib/texts";

import { navLinks } from "./nav-links";
import { StoreLogo } from "./store-logo";

// Pie de la tienda sobre el fondo de acento: marca, frase y secciones.
// Los canales de contacto se suman cuando la API los publique.
export function StoreFooter({ storeName }: { storeName: string }) {
  const tagline = t("store.tagline");

  return (
    <footer aria-label={t("footer.label")} className="bg-accent text-on-accent">
      <div className="mx-auto grid max-w-7xl gap-8 px-4 py-8 md:grid-cols-3 md:gap-10 md:px-16 md:py-12">
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-3">
            <StoreLogo className="size-11" />
            <span className="font-display text-xl font-bold tracking-[0.01em] uppercase md:text-2xl">
              {storeName}
            </span>
          </div>
          {tagline && <p className="text-sm text-on-accent-muted">{tagline}</p>}
        </div>

        <nav aria-label={t("footer.links")}>
          <ul className="flex flex-col gap-1 text-sm">
            {navLinks().map((link) => (
              <li key={link.href}>
                <Link
                  href={link.href}
                  className="inline-flex min-h-11 items-center underline-offset-4 hover:underline md:min-h-8"
                >
                  {link.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      </div>
    </footer>
  );
}
