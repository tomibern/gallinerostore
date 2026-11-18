import { AuthScreen } from "@/components/admin/auth-screen";
import { ForgotPasswordForm } from "@/components/admin/forgot-password-form";
import { t } from "@/lib/texts";

// «Olvidé mi contraseña»: pide el email y manda el link.
export default function ForgotPasswordPage() {
  return (
    <AuthScreen title={t("admin.forgot.title")} subtitle={t("admin.forgot.subtitle")}>
      <ForgotPasswordForm />
    </AuthScreen>
  );
}
