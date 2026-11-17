import { DiagonalBand } from "@/components/store/diagonal-band";
import { LoginForm } from "@/components/admin/login-form";
import { StoreLogo } from "@/components/store/store-logo";
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
    <div className="flex min-h-dvh flex-col bg-[color-mix(in_srgb,var(--color-primary)_8%,white)]">
      <DiagonalBand className="h-3 shrink-0" />
      <main className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center gap-6 px-5 py-6">
        <div className="flex flex-col items-center gap-3 text-center">
          <StoreLogo className="size-28" />
          <h1 className="font-display text-3xl font-bold text-primary uppercase">
            {t("admin.login.title", { store: store?.name ?? "" })}
          </h1>
          <p className="text-sm text-muted">{t("admin.login.subtitle")}</p>
        </div>
        <LoginForm next={typeof next === "string" ? next : null} />
      </main>
    </div>
  );
}
