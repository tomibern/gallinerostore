import type { Metadata } from "next";
import { notFound, permanentRedirect } from "next/navigation";

import { AvailabilityBadge } from "@/components/store/availability-badge";
import { ProductGallery } from "@/components/store/product-gallery";
import { caseLabels, instagramSheetLabels } from "@/components/store/inquiry-labels";
import { ProductInquiry } from "@/components/store/product-inquiry";
import { getProduct, getStore, type SizeStatus } from "@/lib/api";
import { formatPrice } from "@/lib/money";
import { productMetadata, productPath } from "@/lib/seo";
import { t } from "@/lib/texts";

export async function generateMetadata({ params }: PageProps<"/p/[code]">): Promise<Metadata> {
  const [store, result] = await Promise.all([getStore(), getProduct((await params).code)]);
  if (result.status !== "ok") return {};
  return store ? productMetadata(result.product, store) : { title: result.product.name };
}

const SIZE_STATUSES: SizeStatus[] = ["in_stock", "out_of_stock", "on_order"];

// Textos de los botones de consulta según el estado del talle elegido («idle»: sin talle).
function inquiryLabels() {
  const statuses = Object.fromEntries(
    SIZE_STATUSES.map((status) => [status, caseLabels(t(`inquiry.action.${status}`))]),
  ) as Record<SizeStatus, ReturnType<typeof caseLabels>>;
  return {
    ...statuses,
    idle: caseLabels(t("inquiry.action.idle"), t("inquiry.channel.idle")),
    sheet: instagramSheetLabels(),
  };
}

// Detalle del producto: galería, datos, aviso de encargue, selector de talle y consulta.
// El código en la URL va en minúsculas; en mayúsculas redirige (una sola URL por
// producto). Si el producto no existe o no está publicado, la 404 de la tienda.
export default async function ProductPage({ params }: PageProps<"/p/[code]">) {
  const { code } = await params;
  if (code !== code.toLowerCase()) permanentRedirect(productPath(code));

  const [store, result] = await Promise.all([getStore(), getProduct(code)]);
  // Fuera de cualquier try: notFound() corta el render lanzando un error.
  if (result.status === "not_found") notFound();
  if (result.status === "error" || !store) {
    return (
      <main>
        <p className="py-12 text-center text-muted">{t("product.unavailable")}</p>
      </main>
    );
  }

  const { product } = result;
  const price = formatPrice(product.price, product.currency, store.locale, store.price_decimals);
  const onOrder = product.section === "on_order";
  const facts = [
    { label: t("product.category"), value: product.category.name },
    { label: t("product.version"), value: product.version?.name },
    { label: store.collection_label, value: product.collection?.name },
    { label: t("product.season"), value: product.season },
  ].filter((fact): fact is { label: string; value: string } => Boolean(fact.value));

  return (
    <main className="mx-auto grid max-w-7xl gap-6 px-4 py-6 md:grid-cols-2 md:gap-12 md:px-16 md:py-10">
      <ProductGallery
        images={product.images}
        labels={{
          gallery: t("product.gallery.label"),
          pick: product.images.map((_, index) => t("product.gallery.pick", { n: index + 1 })),
        }}
      />

      <div className="flex flex-col gap-5">
        <div className="flex flex-col gap-2">
          <AvailabilityBadge availability={product.availability} className="self-start" />
          <h1 className="font-display text-3xl leading-tight font-bold md:text-4xl">
            {product.name}
          </h1>
          <p className="font-display text-3xl font-bold text-primary">{price}</p>
        </div>

        {onOrder && (
          <p
            data-testid="on-order-notice"
            className="rounded-md border border-border bg-surface p-3 text-sm"
          >
            {product.on_order_notice ?? t("product.onOrderNotice")}
          </p>
        )}

        <ProductInquiry
          sizes={product.sizes}
          labels={{
            legend: t("product.size.legend"),
            choose: t("product.size.choose"),
            outOfStock: t("product.size.outOfStock"),
            status: Object.fromEntries(
              product.sizes.map(({ label, status }) => [
                label,
                t(`product.size.status.${status}`, { size: label }),
              ]),
            ),
            inquiry: inquiryLabels(),
          }}
        />

        {product.description && (
          <p className="text-base leading-relaxed whitespace-pre-line">{product.description}</p>
        )}

        {facts.length > 0 && (
          <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 border-t border-border pt-4 text-sm">
            {facts.map(({ label, value }) => (
              <div key={label} className="contents">
                <dt className="text-muted">{label}</dt>
                <dd>{value}</dd>
              </div>
            ))}
          </dl>
        )}
      </div>
    </main>
  );
}
