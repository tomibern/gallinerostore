"use client";

import Link from "next/link";
import { useState } from "react";

import { AUTH_CARD } from "@/components/admin/auth-screen";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { requestPasswordReset } from "@/lib/admin-api";
import { ADMIN_LOGIN } from "@/lib/admin-paths";
import { t } from "@/lib/texts";

type State = "idle" | "busy" | "sent" | "error";

/** Pide el link. La respuesta es la misma exista o no el email. */
export function ForgotPasswordForm() {
  const [state, setState] = useState<State>("idle");

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setState("busy");
    const result = await requestPasswordReset(String(form.get("email")));
    setState(result === "ok" ? "sent" : "error");
  }

  return (
    <div className="flex flex-col gap-4">
      {state === "sent" ? (
        <p role="status" className={`${AUTH_CARD} text-sm`}>
          {t("admin.forgot.sent")}
        </p>
      ) : (
        <form onSubmit={(event) => void handleSubmit(event)} className={AUTH_CARD}>
          <Label>
            {t("admin.login.email")}
            <Input type="email" name="email" autoComplete="username" required />
          </Label>
          {state === "error" && (
            <p role="alert" className="text-sm font-semibold text-error">
              {t("admin.login.error")}
            </p>
          )}
          <Button type="submit" size="lg" disabled={state === "busy"}>
            {state === "busy" ? t("admin.forgot.submitting") : t("admin.forgot.submit")}
          </Button>
        </form>
      )}
      <Link href={ADMIN_LOGIN} className="self-center text-sm font-semibold underline">
        {t("admin.forgot.backToLogin")}
      </Link>
    </div>
  );
}
