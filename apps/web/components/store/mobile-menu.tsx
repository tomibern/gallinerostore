"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

type Props = {
  links: { href: string; label: string }[];
  labels: { nav: string; open: string };
};

// Menú del celular. La key con la ruta lo vuelve a cerrar al navegar: el
// layout no se desmonta entre páginas.
export function MobileMenu(props: Props) {
  const pathname = usePathname();
  return <Menu key={pathname} pathname={pathname} {...props} />;
}

function Menu({ links, labels, pathname }: Props & { pathname: string }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="md:hidden">
      <button
        type="button"
        aria-label={labels.open}
        aria-expanded={open}
        aria-controls="mobile-menu"
        onClick={() => setOpen(!open)}
        className="flex size-11 cursor-pointer items-center justify-center"
      >
        <svg
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          aria-hidden="true"
        >
          <path d={open ? "M6 6l12 12M18 6L6 18" : "M4 7h16M4 12h16M4 17h16"} />
        </svg>
      </button>
      <nav
        id="mobile-menu"
        aria-label={labels.nav}
        hidden={!open}
        className="absolute inset-x-0 top-full z-20 border-b border-border bg-surface shadow-lg"
      >
        <ul className="flex flex-col py-2">
          {links.map((link) => (
            <li key={link.href}>
              <Link
                href={link.href}
                aria-current={pathname === link.href ? "page" : undefined}
                className="font-display flex min-h-12 items-center px-4 text-xl font-bold uppercase aria-[current=page]:text-primary"
              >
                {link.label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  );
}
