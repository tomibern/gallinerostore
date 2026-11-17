"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { createContext, useContext, useEffect, useState } from "react";

import { LogOutButton } from "@/components/admin/log-out-button";
import { StoreLogo } from "@/components/store/store-logo";
import { Button } from "@/components/ui/button";
import { getAdminSession, type AdminOut } from "@/lib/admin-api";
import { ADMIN_LOGIN } from "@/lib/admin-paths";
import { t } from "@/lib/texts";
import { cn } from "@/lib/utils";

const AdminContext = createContext<AdminOut | null>(null);

/** El admin de la sesión. Solo dentro del panel, donde ya se verificó la sesión. */
export function useAdmin(): AdminOut {
  const admin = useContext(AdminContext);
  if (!admin) throw new Error("useAdmin fuera del panel");
  return admin;
}

type NavItem = { href: string; label: string; short: string; icon: React.ReactNode };

const NAV: NavItem[] = [
  {
    href: "/admin/productos",
    label: t("admin.nav.products"),
    short: t("admin.nav.products"),
    icon: <path d="M8 3l-5 3 2 5 3-1v11h8V10l3 1 2-5-5-3a4 4 0 0 1-8 0z" />,
  },
  {
    href: "/admin/metricas",
    label: t("admin.nav.metrics"),
    short: t("admin.nav.metrics"),
    icon: <path d="M5 20V11M12 20V4M19 20v-6" />,
  },
  {
    href: "/admin/contenido",
    label: t("admin.nav.content"),
    short: t("admin.nav.contentShort"),
    icon: (
      <>
        <rect x="3" y="4" width="18" height="16" rx="1" />
        <path d="M3 15l5-5 4 4 3-3 6 6" />
      </>
    ),
  },
];

function NavIcon({ children }: { children: React.ReactNode }) {
  return (
    <svg
      width="22"
      height="22"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {children}
    </svg>
  );
}

type SessionState = { status: "loading" } | { status: "error" } | { status: "ok"; admin: AdminOut };

/**
 * Esqueleto del panel: verifica la sesión con la API (el proxy de Next solo mira si
 * está la cookie) y dibuja la navegación. Escritorio: barra lateral. Celular: encabezado
 * arriba y secciones abajo, con las mismas funciones.
 */
export function AdminShell({
  storeName,
  children,
}: {
  storeName: string;
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const [session, setSession] = useState<SessionState>({ status: "loading" });
  // Cada «Probar de nuevo» suma uno y vuelve a verificar.
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let active = true;
    getAdminSession()
      .then((admin) => {
        if (!active) return;
        if (admin) setSession({ status: "ok", admin });
        else router.replace(`${ADMIN_LOGIN}?next=${encodeURIComponent(window.location.pathname)}`);
      })
      .catch(() => {
        if (active) setSession({ status: "error" });
      });
    return () => {
      active = false;
    };
  }, [attempt, router]);

  if (session.status === "loading") return null;
  if (session.status === "error") {
    return (
      <main className="mx-auto flex min-h-dvh max-w-md flex-col items-center justify-center gap-4 px-4 text-center">
        <p>{t("admin.unavailable")}</p>
        <Button onClick={() => setAttempt((n) => n + 1)}>{t("admin.retry")}</Button>
      </main>
    );
  }

  const current = NAV.find((item) => pathname.startsWith(item.href));

  return (
    <AdminContext.Provider value={session.admin}>
      <div className="flex min-h-dvh bg-bg md:bg-[color-mix(in_srgb,var(--color-primary)_8%,white)]">
        {/* Escritorio: barra lateral */}
        <aside className="hidden w-60 shrink-0 flex-col gap-1 bg-accent py-5 text-on-accent-muted md:flex">
          <div className="flex items-center gap-2.5 px-4 pb-5">
            <StoreLogo className="size-11" />
            <span className="flex flex-col">
              <span className="font-display text-lg font-bold text-on-accent uppercase">
                {storeName}
              </span>
              <span className="text-xs">{t("admin.panel.label")}</span>
            </span>
          </div>
          <nav aria-label={t("admin.nav.label")} className="flex flex-col gap-1">
            {NAV.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                aria-current={item === current ? "page" : undefined}
                className={cn(
                  "flex min-h-12 items-center px-4 font-semibold hover:text-on-accent",
                  item === current && "bg-primary text-primary-contrast",
                )}
              >
                {item.label}
              </Link>
            ))}
          </nav>
          <div className="flex-1" />
          <Link
            href="/"
            target="_blank"
            className="flex min-h-12 items-center px-4 font-semibold hover:text-on-accent"
          >
            {t("admin.nav.store")} ↗
          </Link>
          <LogOutButton className="flex min-h-12 items-center px-4 text-left font-semibold hover:text-on-accent" />
        </aside>

        <div className="flex min-w-0 flex-1 flex-col pb-20 md:pb-0">
          {/* Celular: encabezado */}
          <header className="border-b border-border bg-surface md:hidden">
            <div className="h-1.5 bg-primary" aria-hidden="true" />
            <div className="flex h-14 items-center gap-2.5 pr-2 pl-4">
              <StoreLogo className="size-8" />
              <span className="flex-1 font-display text-xl font-bold uppercase">
                {current?.short ?? t("admin.panel.label")}
              </span>
              <Link
                href="/"
                target="_blank"
                className="flex min-h-11 items-center px-2 text-sm font-semibold"
              >
                {t("admin.nav.store")}
              </Link>
            </div>
          </header>

          <main className="flex-1 px-4 py-5 md:px-10 md:py-8">{children}</main>

          {/* Celular: secciones abajo */}
          <nav
            aria-label={t("admin.nav.label")}
            className="fixed inset-x-0 bottom-0 grid h-17 grid-cols-3 bg-accent md:hidden"
          >
            {NAV.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                aria-current={item === current ? "page" : undefined}
                className={cn(
                  "flex flex-col items-center justify-center gap-1 border-t-4 border-transparent text-xs font-semibold text-on-accent-muted",
                  item === current && "border-primary font-bold text-on-accent",
                )}
              >
                <NavIcon>{item.icon}</NavIcon>
                {item.short}
              </Link>
            ))}
          </nav>
        </div>
      </div>
    </AdminContext.Provider>
  );
}
