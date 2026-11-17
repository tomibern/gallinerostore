import { AdminShell } from "@/components/admin/admin-shell";
import { getStore } from "@/lib/api";

// Panel del admin: todo lo que va detrás del login.
export default async function PanelLayout({ children }: { children: React.ReactNode }) {
  const store = await getStore();
  return <AdminShell storeName={store?.name ?? ""}>{children}</AdminShell>;
}
