import { AuthScreen } from "@/components/admin/auth-screen";
import { LoginForm } from "@/components/admin/login-form";
import { getStore } from "@/lib/api";
import { t } from "@/lib/texts";

// Login del admin: la misma tarjeta en celular y escritorio, centrada.
export default async function AdminLoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string | string[] }>;
}) {
  const [{ next }, store] = await Promise.all([searchParams, getStore()]);

  return (
    <AuthScreen
      title={t("admin.login.title", { store: store?.name ?? "" })}
      subtitle={t("admin.login.subtitle")}
    >
      <LoginForm next={typeof next === "string" ? next : null} />
    </AuthScreen>
  );
}
