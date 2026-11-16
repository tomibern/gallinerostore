import type { Metadata } from "next";
import { notFound, permanentRedirect } from "next/navigation";

import { AvailabilityBadge } from "@/components/store/availability-badge";
import { ProductGallery } from "@/components/store/product-gallery";
import { ProductInquiry } from "@/components/store/product-inquiry";
import { getProduct, getStore, type Channel, type SizeStatus } from "@/lib/api";
import { formatPrice } from "@/lib/money";
import { t } from "@/lib/texts";

export async function generateMetadata({ params }: PageProps<"/p/[code]">): Promise<Metadata> {
  const result = await getProduct((await params).code);
  return result.status === "ok" ? { title: result.product.name } : {};
}

const CHANNELS: Channel[] = ["whatsapp", "instagram"];
const SIZE_STATUSES: SizeStatus[] = ["in_stock", "out_of_stock", "on_order"];

// Textos de los botones de consulta según el estado del talle elegido («idle»: sin talle).
function inquiryLabels() {
  const byCase = (action: string, buttonAction: string) => ({
    action,
    channels: Object.fromEntries(
      CHANNELS.map((channel) => {
        const short = t(`inquiry.channel.${channel}`);
        return [
          channel,
          { short, long: t("inquiry.channel.long", { action: buttonAction, channel: short }) },
        ];
      }),
    ) as Record<Channel, { short: string; long: string }>,
  });
  const statuses = Object.fromEntries(
    SIZE_STATUSES.map((status) => {
      const action = t(`inquiry.action.${status}`);
      return [status, byCase(action, action)];
    }),
  ) as Record<SizeStatus, ReturnType<typeof byCase>>;
  return {
    ...statuses,
    idle: byCase(t("inquiry.action.idle"), t("inquiry.channel.idle")),
    sheet: {
      title: t("inquiry.sheet.title"),
      text: t("inquiry.sheet.text"),
      copy: t("inquiry.sheet.copy"),
      copied: t("inquiry.sheet.copied"),
      copyFailed: t("inquiry.sheet.copyFailed"),
      open: t("inquiry.sheet.open"),
      close: t("inquiry.sheet.close"),
    },
  };
}

// Detalle del producto: galería, datos, aviso de encargue, selector de talle y consulta.
// El código en la URL va en minúsculas; en mayúsculas redirige (una sola URL por
// producto). Si el producto no existe o no está publicado, la 404 de la tienda.
export default async function ProductPage({ params }: PageProps<"/p/[code]">) {
  const { code } = await params;
  if (code !== code.toLowerCase()) permanentRedirect(`/p/${code.toLowerCase()}`);

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
