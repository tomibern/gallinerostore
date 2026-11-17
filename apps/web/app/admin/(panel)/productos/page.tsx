import { AdminPage } from "@/components/admin/admin-page";
import { t } from "@/lib/texts";

export default function AdminProductsPage() {
  return (
    <AdminPage title={t("admin.nav.products")}>
      <p className="text-muted">{t("admin.empty")}</p>
    </AdminPage>
  );
}
