import { AdminPage } from "@/components/admin/admin-page";
import { t } from "@/lib/texts";

export default function AdminMetricsPage() {
  return (
    <AdminPage title={t("admin.nav.metrics")}>
      <p className="text-muted">{t("admin.empty")}</p>
    </AdminPage>
  );
}
