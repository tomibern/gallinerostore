import { AuthScreen } from "@/components/admin/auth-screen";
import { ChoosePasswordForm } from "@/components/admin/choose-password-form";
import { t } from "@/lib/texts";

// «Elegir contraseña», desde el link del email (recuperación o invitación). El token
// llega en el fragmento de la dirección: lo lee el formulario en el navegador.
export default function ChoosePasswordPage() {
  return (
    <AuthScreen title={t("admin.choose.title")} subtitle={t("admin.choose.subtitle")}>
      <ChoosePasswordForm />
    </AuthScreen>
  );
}
