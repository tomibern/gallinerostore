"use client";

import { useRouter } from "next/navigation";
import { useReducer, useRef, useState } from "react";

import { useAdmin } from "@/components/admin/admin-shell";
import { LogOutButton } from "@/components/admin/log-out-button";
import { NewPasswordFields, readNewPassword } from "@/components/admin/new-password-fields";
import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { changePassword } from "@/lib/admin-api";
import { ADMIN_LOGIN } from "@/lib/admin-paths";
import {
  PASSWORD_CHANGE_CLOSED,
  passwordChangeError,
  passwordChangeReducer,
  type PasswordChangeAction,
} from "@/lib/password-change";
import { t } from "@/lib/texts";

// Cuenta: quién entró, cambiar la contraseña (un formulario que se abre a pedido) y
// cerrar sesión (en el celular, el único lugar para salir).
export function AccountSection() {
  const admin = useAdmin();
  const router = useRouter();
  const toggleRef = useRef<HTMLButtonElement>(null);
  const [busy, setBusy] = useState(false);
  const [{ open, feedback }, dispatch] = useReducer(passwordChangeReducer, PASSWORD_CHANGE_CLOSED);

  function close(action: Extract<PasswordChangeAction, { type: "cancel" | "saved" }>) {
    dispatch(action);
    // El foco vuelve al botón que abrió el formulario, que deja de existir al cerrarse.
    requestAnimationFrame(() => toggleRef.current?.focus());
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const read = readNewPassword(form);
    if ("error" in read) {
      dispatch({ type: "failed", text: read.error });
      return;
    }
    setBusy(true);
    const result = await changePassword({
      current_password: String(form.get("currentPassword")),
      new_password: read.password,
    });
    setBusy(false);
    if (result === "ok") close({ type: "saved" });
    else if (result === "unauthorized") router.replace(ADMIN_LOGIN);
    else dispatch({ type: "failed", text: passwordChangeError(result) });
  }

  const message = feedback && (
    <p
      role={feedback.kind === "error" ? "alert" : "status"}
      className={
        feedback.kind === "error" ? "text-sm font-semibold text-error" : "text-sm font-semibold"
      }
    >
      {feedback.text}
    </p>
  );

  return (
    <section className="flex max-w-xl flex-col gap-3 bg-surface p-6">
      <h2 className="font-display text-2xl font-bold uppercase">{t("admin.account.title")}</h2>
      <p className="text-sm">{t("admin.account.signedInAs", { email: admin.email })}</p>

      {open ? (
        <form
          aria-label={t("admin.account.passwordTitle")}
          onSubmit={(event) => void handleSubmit(event)}
          className="flex flex-col gap-4 border-t border-border pt-4"
          noValidate
        >
          <h3 className="font-semibold">{t("admin.account.passwordTitle")}</h3>
          {/* Para el gestor de contraseñas: de qué cuenta es. */}
          <input
            type="email"
            name="username"
            autoComplete="username"
            value={admin.email}
            readOnly
            hidden
          />
          <Label>
            {t("admin.account.currentPassword")}
            <Input
              type="password"
              name="currentPassword"
              autoComplete="current-password"
              autoFocus
              required
            />
          </Label>
          <NewPasswordFields />
          {message}
          <div className="flex flex-wrap gap-3">
            <Button type="submit" disabled={busy}>
              {busy ? t("admin.account.submitting") : t("admin.account.submit")}
            </Button>
            <Button
              type="button"
              variant="outline"
              disabled={busy}
              onClick={() => close({ type: "cancel" })}
            >
              {t("admin.account.cancel")}
            </Button>
          </div>
        </form>
      ) : (
        <div className="flex flex-col items-start gap-3 border-t border-border pt-4">
          {message}
          <Button
            ref={toggleRef}
            type="button"
            variant="outline"
            onClick={() => dispatch({ type: "open" })}
          >
            {t("admin.account.open")}
          </Button>
        </div>
      )}

      <LogOutButton className={buttonVariants({ variant: "outline", className: "self-start" })} />
    </section>
  );
}
