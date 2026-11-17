"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { getAdminSession, logIn, type LoginResult } from "@/lib/admin-api";
import { afterLoginPath } from "@/lib/admin-paths";
import { t } from "@/lib/texts";

const ERRORS: Record<Exclude<LoginResult, "ok">, string> = {
  invalid: t("admin.login.invalid"),
  too_many: t("admin.login.tooMany"),
  error: t("admin.login.error"),
};

/** Formulario de login. Si ya hay sesión, sigue de largo al panel. */
export function LoginForm({ next }: { next: string | null }) {
  const router = useRouter();
  const destination = afterLoginPath(next);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAdminSession()
      .then((admin) => {
        if (admin) router.replace(destination);
      })
      .catch(() => {});
  }, [destination, router]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setBusy(true);
    setError(null);
    const result = await logIn({
      email: String(form.get("email")),
      password: String(form.get("password")),
      remember: form.get("remember") === "on",
    });
    if (result === "ok") {
      router.replace(destination);
      return;
    }
    setError(ERRORS[result]);
    setBusy(false);
  }

  return (
    <form
      onSubmit={(event) => void handleSubmit(event)}
      className="flex flex-col gap-4 bg-surface px-5 py-6 shadow-[0_8px_24px_rgb(110_18_25/0.12)]"
    >
      <Label>
        {t("admin.login.email")}
        <Input type="email" name="email" autoComplete="username" required />
      </Label>
      <Label>
        {t("admin.login.password")}
        <Input type="password" name="password" autoComplete="current-password" required />
      </Label>
      <label className="flex items-center gap-2.5 text-sm">
        <input
          type="checkbox"
          name="remember"
          defaultChecked
          className="size-5 shrink-0 accent-primary"
        />
        {t("admin.login.remember")}
      </label>
      {error && (
        <p role="alert" className="text-sm font-semibold text-error">
          {error}
        </p>
      )}
      <Button type="submit" size="lg" disabled={busy}>
        {busy ? t("admin.login.submitting") : t("admin.login.submit")}
      </Button>
    </form>
  );
}
