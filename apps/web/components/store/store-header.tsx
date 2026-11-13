import Link from "next/link";

import { t } from "@/lib/texts";

import { MobileMenu } from "./mobile-menu";
import { navLinks } from "./nav-links";
import { StoreLogo } from "./store-logo";

// Encabezado de la tienda: franja de color, logo y nombre, y la navegación
// (en celular, detrás del botón de menú).
export function StoreHeader({ storeName }: { storeName: string }) {
  const links = navLinks();

  return (
    <header className="relative border-b border-border bg-surface">
      <div aria-hidden="true" className="h-3 bg-primary" />
      <div className="mx-auto flex h-15 max-w-7xl items-center justify-between gap-10 pr-2 pl-4 md:h-20 md:px-16">
        <Link href="/" className="flex min-w-0 items-center gap-2.5 md:gap-3">
          <StoreLogo className="size-9 md:size-12" />
          <span className="font-display truncate text-[19px] font-bold tracking-[0.01em] text-primary uppercase md:text-2xl">
            {storeName}
          </span>
        </Link>

        <nav aria-label={t("nav.label")} className="mr-auto hidden md:block">
          <ul className="flex gap-7 text-[15px] font-semibold">
            {links.map((link) => (
              <li key={link.href}>
                <Link href={link.href} className="hover:text-primary">
                  {link.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>

        <MobileMenu links={links} labels={{ nav: t("nav.label"), open: t("nav.menuOpen") }} />
      </div>
    </header>
  );
}
