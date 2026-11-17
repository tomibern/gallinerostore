"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { logOut } from "@/lib/admin-api";
import { ADMIN_LOGIN } from "@/lib/admin-paths";
import { t } from "@/lib/texts";

/** Cierra la sesión y vuelve al login. Aunque la API no responda, sale del panel. */
export function LogOutButton({ className }: { className?: string }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);

  async function handleClick() {
    setBusy(true);
    try {
      await logOut();
    } finally {
      router.replace(ADMIN_LOGIN);
    }
  }

  return (
    <button type="button" className={className} disabled={busy} onClick={() => void handleClick()}>
      {t("admin.nav.logOut")}
    </button>
  );
}
