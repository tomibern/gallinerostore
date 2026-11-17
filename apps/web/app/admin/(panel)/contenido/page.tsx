import { AccountSection } from "@/components/admin/account-section";
import { AdminPage } from "@/components/admin/admin-page";
import { t } from "@/lib/texts";

export default function AdminContentPage() {
  return (
    <AdminPage title={t("admin.nav.content")}>
      <AccountSection />
    </AdminPage>
  );
}
