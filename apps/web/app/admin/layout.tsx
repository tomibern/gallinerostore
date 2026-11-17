import type { Metadata } from "next";

import { t } from "@/lib/texts";

export const dynamic = "force-dynamic";

// El panel no se indexa (robots.txt también excluye /admin).
export const metadata: Metadata = {
  title: t("admin.meta.title"),
  robots: { index: false, follow: false },
};

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return children;
}
