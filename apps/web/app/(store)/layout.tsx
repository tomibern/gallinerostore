import { StoreFooter } from "@/components/store/store-footer";
import { StoreHeader } from "@/components/store/store-header";
import { getStore } from "@/lib/api";
import { t } from "@/lib/texts";

export const dynamic = "force-dynamic";

// Layout de la tienda pública: encabezado, contenido y pie.
export default async function StoreLayout({ children }: { children: React.ReactNode }) {
  const store = await getStore();

  if (!store) {
    return (
      <main className="mx-auto flex min-h-dvh max-w-xl items-center px-4 text-center">
        <p className="text-lg">{t("store.unavailable")}</p>
      </main>
    );
  }

  return (
    <div className="flex min-h-dvh flex-col">
      <StoreHeader storeName={store.name} />
      <div className="flex-1">{children}</div>
      <StoreFooter storeName={store.name} />
    </div>
  );
}
