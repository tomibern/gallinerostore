"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AUTH_CARD } from "@/components/admin/auth-screen";
import {
  NewPasswordFields,
  readNewPassword,
  TOO_SHORT,
} from "@/components/admin/new-password-fields";
import { Button } from "@/components/ui/button";
import { confirmPasswordReset } from "@/lib/admin-api";
import { ADMIN_FORGOT_PASSWORD, ADMIN_HOME } from "@/lib/admin-paths";
import { t } from "@/lib/texts";

/** El token del link: va en el fragmento (`#token=…`), que no viaja al servidor. */
function tokenFromHash(hash: string): string | null {
  return new URLSearchParams(hash.replace(/^#/, "")).get("token");
}

/** Elige la contraseña con el token del link y entra al panel. */
export function ChoosePasswordForm() {
  const router = useRouter();
  // undefined: todavía no se leyó la dirección (en el servidor no hay fragmento).
  const [token, setToken] = useState<string | null | undefined>(undefined);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [invalid, setInvalid] = useState(false);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- el fragmento solo existe en el navegador
    setToken(tokenFromHash(window.location.hash));
  }, []);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) return;
    const read = readNewPassword(new FormData(event.currentTarget));
    if ("error" in read) {
      setError(read.error);
      return;
    }
    setBusy(true);
    setError(null);
    const result = await confirmPasswordReset({ token, password: read.password });
    if (result === "ok") {
      router.replace(ADMIN_HOME);
      return;
    }
    if (result === "invalid") setInvalid(true);
    else if (result === "too_short") setError(TOO_SHORT);
    else setError(t("admin.login.error"));
    setBusy(false);
  }

  if (token === undefined) return null;
  if (token === null || invalid) {
    return (
      <div className={AUTH_CARD}>
        <p role="alert" className="text-sm font-semibold text-error">
          {t("admin.choose.invalid")}
        </p>
        <Link href={ADMIN_FORGOT_PASSWORD} className="text-sm font-semibold underline">
          {t("admin.choose.requestNew")}
        </Link>
      </div>
    );
  }

  return (
    <form onSubmit={(event) => void handleSubmit(event)} className={AUTH_CARD} noValidate>
      <NewPasswordFields />
      {error && (
        <p role="alert" className="text-sm font-semibold text-error">
          {error}
        </p>
      )}
      <Button type="submit" size="lg" disabled={busy}>
        {busy ? t("admin.choose.submitting") : t("admin.choose.submit")}
      </Button>
    </form>
  );
}
