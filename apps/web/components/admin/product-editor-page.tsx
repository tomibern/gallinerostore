import { ProductEditor } from "@/components/admin/product-editor";
import { getStore } from "@/lib/api";
import { t } from "@/lib/texts";

/** El editor con la moneda, el idioma y los decimales de la tienda (ADR 0002). */
export async function ProductEditorPage({ code }: { code: string | null }) {
  const store = await getStore();
  if (!store) return <p role="alert">{t("admin.editor.loadError")}</p>;
  return (
    <ProductEditor
      code={code}
      priceFormat={{
        currency: store.currency,
        locale: store.locale,
        decimals: store.price_decimals,
      }}
    />
  );
}
