import { AccountSection } from "@/components/admin/account-section";
import { AdminPage } from "@/components/admin/admin-page";
import { ContactSection } from "@/components/admin/contact-section";
import { getStore } from "@/lib/api";
import { t } from "@/lib/texts";

export default async function AdminContentPage() {
  const features = (await getStore())?.features;
  return (
    <AdminPage title={t("admin.nav.content")}>
      <ContactSection
        instagram={features?.instagram ?? true}
        onOrder={features?.on_order ?? true}
      />
      <AccountSection />
    </AdminPage>
  );
}
