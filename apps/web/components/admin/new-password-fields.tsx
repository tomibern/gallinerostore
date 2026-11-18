import { useId } from "react";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { MIN_PASSWORD_LENGTH, newPasswordProblem } from "@/lib/admin-paths";
import { t } from "@/lib/texts";

/** Contraseña nueva y su repetición, con el gestor de contraseñas habilitado. */
export function NewPasswordFields() {
  const hintId = useId();
  return (
    <>
      <div className="flex flex-col gap-1.5">
        <Label>
          {t("admin.password.new")}
          <Input
            type="password"
            name="newPassword"
            autoComplete="new-password"
            minLength={MIN_PASSWORD_LENGTH}
            aria-describedby={hintId}
            required
          />
        </Label>
        <p id={hintId} className="text-xs text-muted">
          {t("admin.password.hint", { min: MIN_PASSWORD_LENGTH })}
        </p>
      </div>
      <Label>
        {t("admin.password.repeat")}
        <Input
          type="password"
          name="repeatPassword"
          autoComplete="new-password"
          minLength={MIN_PASSWORD_LENGTH}
          required
        />
      </Label>
    </>
  );
}

export const TOO_SHORT = t("admin.password.tooShort", { min: MIN_PASSWORD_LENGTH });

/** La contraseña nueva del formulario, o el error a mostrar si no sirve. */
export function readNewPassword(form: FormData): { password: string } | { error: string } {
  const password = String(form.get("newPassword"));
  const problem = newPasswordProblem(password, String(form.get("repeatPassword")));
  if (problem === "short") {
    return { error: TOO_SHORT };
  }
  if (problem === "mismatch") return { error: t("admin.password.mismatch") };
  return { password };
}
