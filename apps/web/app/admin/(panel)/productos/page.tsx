import { Suspense } from "react";

import { AdminPage } from "@/components/admin/admin-page";
import { ProductList } from "@/components/admin/product-list";
import { getStore } from "@/lib/api";
import { t } from "@/lib/texts";

export default async function AdminProductsPage() {
  // Moneda y decimales salen de la tienda, como en el catálogo público.
  const store = await getStore();
  return (
    <AdminPage title={t("admin.nav.products")}>
      {store ? (
        // useSearchParams necesita un Suspense alrededor.
        <Suspense>
          <ProductList priceFormat={{ locale: store.locale, decimals: store.price_decimals }} />
        </Suspense>
      ) : (
        <p role="alert">{t("admin.products.error")}</p>
      )}
    </AdminPage>
  );
}
