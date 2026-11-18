"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { useAdmin } from "@/components/admin/admin-shell";
import { LogOutButton } from "@/components/admin/log-out-button";
import {
  NewPasswordFields,
  readNewPassword,
  TOO_SHORT,
} from "@/components/admin/new-password-fields";
import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { changePassword } from "@/lib/admin-api";
import { ADMIN_LOGIN } from "@/lib/admin-paths";
import { t } from "@/lib/texts";

type Feedback = { kind: "error" | "done"; text: string } | null;

// Cuenta: quién entró, cambiar la contraseña y cerrar sesión (en el celular, el único
// lugar para salir).
export function AccountSection() {
  const admin = useAdmin();
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState<Feedback>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const read = readNewPassword(form);
    if ("error" in read) {
      setFeedback({ kind: "error", text: read.error });
      return;
    }
    setBusy(true);
    setFeedback(null);
    const result = await changePassword({
      current_password: String(form.get("currentPassword")),
      new_password: read.password,
    });
    setBusy(false);
    if (result === "ok") {
      formElement.reset();
      setFeedback({ kind: "done", text: t("admin.account.done") });
    } else if (result === "unauthorized") {
      router.replace(ADMIN_LOGIN);
    } else {
      setFeedback({
        kind: "error",
        text:
          result === "wrong_current"
            ? t("admin.account.wrongCurrent")
            : result === "too_short"
              ? TOO_SHORT
              : t("admin.login.error"),
      });
    }
  }

  return (
    <section className="flex max-w-xl flex-col gap-3 bg-surface p-6">
      <h2 className="font-display text-2xl font-bold uppercase">{t("admin.account.title")}</h2>
      <p className="text-sm">{t("admin.account.signedInAs", { email: admin.email })}</p>

      <form
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
          <Input type="password" name="currentPassword" autoComplete="current-password" required />
        </Label>
        <NewPasswordFields />
        {feedback && (
          <p
            role={feedback.kind === "error" ? "alert" : "status"}
            className={
              feedback.kind === "error"
                ? "text-sm font-semibold text-error"
                : "text-sm font-semibold"
            }
          >
            {feedback.text}
          </p>
        )}
        <Button type="submit" variant="outline" className="self-start" disabled={busy}>
          {busy ? t("admin.account.submitting") : t("admin.account.submit")}
        </Button>
      </form>

      <LogOutButton className={buttonVariants({ variant: "outline", className: "self-start" })} />
    </section>
  );
}
