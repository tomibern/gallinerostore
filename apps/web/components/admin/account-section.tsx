"use client";

import { useAdmin } from "@/components/admin/admin-shell";
import { LogOutButton } from "@/components/admin/log-out-button";
import { buttonVariants } from "@/components/ui/button";
import { t } from "@/lib/texts";

// Cuenta: quién entró y cerrar sesión (en el celular, el único lugar para salir).
export function AccountSection() {
  const admin = useAdmin();

  return (
    <section className="flex max-w-xl flex-col gap-3 bg-surface p-6">
      <h2 className="font-display text-2xl font-bold uppercase">{t("admin.account.title")}</h2>
      <p className="text-sm">{t("admin.account.signedInAs", { email: admin.email })}</p>
      <LogOutButton className={buttonVariants({ variant: "outline", className: "self-start" })} />
    </section>
  );
}
