"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  createAdminProduct,
  getAdminProduct,
  getCatalogOptions,
  updateAdminProduct,
  type AdminProduct,
  type CatalogOptions,
  type SaleMode,
} from "@/lib/admin-api";
import { ADMIN_HOME, ADMIN_LOGIN, adminProductPath } from "@/lib/admin-paths";
import {
  categoryLabels,
  emptyForm,
  groupRange,
  productBody,
  productForm,
  showsCollection,
  stockSizes,
  type PriceFormat,
  type ProductForm,
  type SizeChoice,
} from "@/lib/admin-product";
import type { FieldErrors } from "@/lib/admin-settings";
import { currencySymbol } from "@/lib/money";
import { t } from "@/lib/texts";
import { cn } from "@/lib/utils";

const SALE_MODES: SaleMode[] = ["stock", "on_order"];

type Loaded = { options: CatalogOptions; product: AdminProduct | null };
type LoadState = { kind: "loading" } | { kind: "error" } | { kind: "not_found" } | Loaded;

type Status =
  | { kind: "idle" }
  | { kind: "saving" }
  | { kind: "saved" }
  | { kind: "invalid" }
  | { kind: "error" };

const fieldClass =
  "h-12 w-full border border-border bg-surface px-3 text-base font-normal text-text focus-visible:border-accent focus-visible:outline-2 focus-visible:outline-primary aria-invalid:border-error md:h-11";

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="flex flex-col gap-4 bg-surface px-4 py-5 md:p-6">
      <h2 className="font-display text-xl font-bold text-accent uppercase md:text-2xl">{title}</h2>
      {children}
    </section>
  );
}

function FieldError({ id, error }: { id: string; error?: string }) {
  if (!error) return null;
  return (
    <span id={id} className="text-sm font-semibold text-error">
      {error}
    </span>
  );
}

function Hint({ id, children }: { id?: string; children: React.ReactNode }) {
  return (
    <span id={id} className="text-xs leading-snug font-normal text-muted">
      {children}
    </span>
  );
}

/** Etiqueta, control y error de un campo (el lector de pantalla lee el error). */
function Field({
  id,
  label,
  hint,
  error,
  children,
}: {
  id: string;
  label: string;
  hint?: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1.5 text-sm font-semibold">
      <label htmlFor={id} className="flex flex-wrap items-baseline gap-x-2">
        {label}
        {hint && <Hint>{hint}</Hint>}
      </label>
      {children}
      <FieldError id={`${id}-error`} error={error} />
    </div>
  );
}

function invalidProps(id: string, error?: string) {
  return error ? { "aria-invalid": true, "aria-describedby": `${id}-error` } : {};
}

/** Botones de una sola opción (versión, modo de venta), como en los wireframes. */
function Segmented<T extends string | null>({
  label,
  options,
  value,
  onChange,
  strong,
}: {
  label: string;
  options: { value: T; label: string }[];
  value: T;
  onChange: (value: T) => void;
  strong?: boolean;
}) {
  return (
    <div
      role="radiogroup"
      aria-label={label}
      className={cn("grid border-accent", strong ? "border-2" : "border")}
      style={{ gridTemplateColumns: `repeat(${options.length}, minmax(0, 1fr))` }}
    >
      {options.map((option) => {
        const checked = option.value === value;
        return (
          <button
            key={option.value ?? ""}
            type="button"
            role="radio"
            aria-checked={checked}
            onClick={() => onChange(option.value)}
            className={cn(
              "min-h-12 px-2 text-sm md:min-h-11",
              checked
                ? "bg-accent font-bold text-on-accent"
                : "bg-surface font-semibold text-accent",
            )}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}

function SizeGrid({ sizes, onToggle }: { sizes: SizeChoice[]; onToggle: (label: string) => void }) {
  return (
    <ul className="flex flex-col md:grid md:grid-cols-[repeat(auto-fill,minmax(96px,1fr))] md:gap-2.5">
      {sizes.map((size) => {
        const state = t(
          size.inStock ? "admin.editor.size.inStock" : "admin.editor.size.outOfStock",
        );
        return (
          <li key={size.label}>
            <button
              type="button"
              aria-pressed={size.inStock}
              aria-label={`${size.label} · ${state}`}
              data-size={size.label}
              onClick={() => onToggle(size.label)}
              className={cn(
                // Celular: una fila por talle con su estado a la derecha.
                "flex min-h-13 w-full items-center justify-between border-b border-border px-1 text-accent",
                // Escritorio: una tarjeta por talle.
                "md:h-21 md:flex-col md:justify-center md:gap-1 md:border-2",
                size.inStock
                  ? "md:border-primary md:bg-primary md:text-primary-contrast"
                  : "md:border-dashed md:border-primary/60 md:bg-surface md:text-muted md:line-through",
              )}
            >
              <span className="text-lg font-bold md:text-2xl">{size.label}</span>
              <span
                className={cn(
                  "min-w-32 px-2.5 py-2 text-center text-[13px] md:min-w-0 md:p-0 md:text-xs",
                  size.inStock
                    ? "bg-primary font-bold text-primary-contrast md:bg-transparent"
                    : "border border-dashed border-primary/60 font-semibold text-muted line-through md:border-0",
                )}
              >
                {state}
              </span>
            </button>
          </li>
        );
      })}
    </ul>
  );
}

/**
 * Editor de un producto: nuevo (`code` null) o existente. Carga las opciones del
 * catálogo y el producto, y guarda todo junto. Fotos, historia, estado y destacado
 * se suman en otros tickets.
 */
export function ProductEditor({
  code,
  priceFormat,
}: {
  code: string | null;
  priceFormat: PriceFormat;
}) {
  const router = useRouter();
  const [attempt, setAttempt] = useState(0);
  const [loaded, setLoaded] = useState<LoadState>({ kind: "loading" });
  const [form, setForm] = useState<ProductForm | null>(null);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [status, setStatus] = useState<Status>({ kind: "idle" });

  const toLogin = useCallback(() => {
    const next = window.location.pathname + window.location.search;
    router.replace(`${ADMIN_LOGIN}?next=${encodeURIComponent(next)}`);
  }, [router]);

  useEffect(() => {
    let active = true;
    Promise.all([getCatalogOptions(), code ? getAdminProduct(code) : Promise.resolve(null)])
      .then(([options, product]) => {
        if (!active) return;
        if (!options || (code && product === null)) return toLogin();
        if (product === "not_found") return setLoaded({ kind: "not_found" });
        setLoaded({ options, product });
        setForm(product ? productForm(product, priceFormat) : emptyForm(options));
      })
      .catch(() => {
        if (active) setLoaded({ kind: "error" });
      });
    return () => {
      active = false;
    };
  }, [code, attempt, priceFormat, toLogin]);

  if ("kind" in loaded) {
    if (loaded.kind === "loading") {
      return (
        <p role="status" className="text-muted">
          {t("admin.editor.loading")}
        </p>
      );
    }
    return (
      <div role="alert" className="flex flex-col items-start gap-3">
        <p>{t(loaded.kind === "not_found" ? "admin.editor.notFound" : "admin.editor.loadError")}</p>
        {loaded.kind === "error" ? (
          <Button variant="outline" onClick={() => setAttempt((n) => n + 1)}>
            {t("admin.retry")}
          </Button>
        ) : (
          <Link href={ADMIN_HOME} className="font-semibold underline">
            {t("admin.editor.back")}
          </Link>
        )}
      </div>
    );
  }
  if (!form) return null;

  const { options, product } = loaded;
  const sizes = form.saleMode === "stock" ? stockSizes(options, form, product) : [];
  const range = groupRange(options, form.category);
  const isDraft = !product || product.status === "draft";

  function update(changes: Partial<ProductForm>) {
    setForm((current) => (current ? { ...current, ...changes } : current));
    setStatus({ kind: "idle" });
  }

  function toggleSize(label: string) {
    update({
      sizes: sizes.map((size) =>
        size.label === label ? { ...size, inStock: !size.inStock } : size,
      ),
    });
  }

  function toggleTag(slug: string) {
    if (!form) return;
    update({
      tags: form.tags.includes(slug)
        ? form.tags.filter((tag) => tag !== slug)
        : [...form.tags, slug],
    });
  }

  async function save(event: React.FormEvent) {
    event.preventDefault();
    if (!form || status.kind === "saving") return;
    const prepared = productBody(form, sizes, options, priceFormat);
    if ("priceError" in prepared) {
      setErrors((current) => ({ ...current, price: prepared.priceError }));
      setStatus({ kind: "invalid" });
      return;
    }
    setStatus({ kind: "saving" });
    const result = product
      ? await updateAdminProduct(product.code, prepared.body)
      : await createAdminProduct(prepared.body);
    if (result.status === "ok") {
      setErrors({});
      setStatus({ kind: "saved" });
      setLoaded({ options, product: result.data });
      setForm(productForm(result.data, priceFormat));
      // Un producto nuevo ya tiene código: la URL pasa a ser la de su editor. Sin
      // navegar, para no volver a cargar y perder el aviso de guardado.
      if (!product) window.history.replaceState(null, "", adminProductPath(result.data.code));
    } else if (result.status === "invalid") {
      setErrors(result.errors);
      setStatus({ kind: "invalid" });
    } else if (result.status === "unauthorized") {
      toLogin();
    } else {
      setStatus({ kind: "error" });
    }
  }

  const statusText =
    status.kind === "saving"
      ? t("admin.editor.saving")
      : status.kind === "saved"
        ? t("admin.editor.saved")
        : status.kind === "invalid"
          ? t("admin.editor.invalid")
          : status.kind === "error"
            ? t("admin.editor.saveError")
            : "";

  const title = product ? product.name : t("admin.editor.newTitle");
  const symbol = currencySymbol(priceFormat.currency, priceFormat.locale);

  return (
    <form onSubmit={save} noValidate className="flex flex-col gap-4 pb-28 md:gap-5 md:pb-0">
      <div className="flex flex-wrap items-center gap-x-3.5 gap-y-2">
        <Link href={ADMIN_HOME} className="text-sm font-semibold text-accent hover:text-primary">
          <span aria-hidden="true" className="md:hidden">
            ←
          </span>
          <span className="sr-only md:not-sr-only">{t("admin.editor.back")}</span>
          <span className="sr-only md:hidden">{t("admin.editor.backShort")}</span>
        </Link>
        <h1 className="flex-1 font-display text-2xl font-bold text-accent uppercase md:text-4xl">
          {title}
        </h1>
        {product && (
          <span
            data-product-code={product.code}
            title={t("admin.editor.code")}
            className="border border-border bg-surface px-2 py-1 text-xs font-bold md:text-sm"
          >
            {product.code}
          </span>
        )}
        {product?.status === "published" && (
          <a
            href={`/p/${product.code.toLowerCase()}`}
            target="_blank"
            rel="noreferrer"
            className="text-sm font-semibold text-accent hover:text-primary"
          >
            {t("admin.editor.viewInStore")}
          </a>
        )}
      </div>

      <div className="flex flex-col gap-3 md:flex-row md:items-start md:gap-5">
        <div className="flex min-w-0 flex-1 flex-col gap-3 md:gap-4">
          <Card title={t("admin.editor.data")}>
            <Field id="name" label={t("admin.editor.name")} error={errors.name}>
              <input
                id="name"
                value={form.name}
                onChange={(event) => update({ name: event.target.value })}
                maxLength={200}
                className={fieldClass}
                {...invalidProps("name", errors.name)}
              />
            </Field>
            <div className="grid gap-4 md:grid-cols-2">
              <Field id="category" label={t("admin.editor.category")} error={errors.category}>
                <select
                  id="category"
                  value={form.category}
                  onChange={(event) => update({ category: event.target.value })}
                  className={fieldClass}
                  {...invalidProps("category", errors.category)}
                >
                  {!form.category && (
                    <option value="" disabled>
                      {t("admin.editor.categoryPlaceholder")}
                    </option>
                  )}
                  {categoryLabels(options).map((category) => (
                    <option key={category.slug} value={category.slug}>
                      {category.label}
                    </option>
                  ))}
                </select>
              </Field>
              <Field
                id="season"
                label={t("admin.editor.season")}
                hint={t("admin.editor.optional")}
                error={errors.season}
              >
                <input
                  id="season"
                  value={form.season}
                  onChange={(event) => update({ season: event.target.value })}
                  maxLength={40}
                  className={fieldClass}
                  {...invalidProps("season", errors.season)}
                />
              </Field>
            </div>
            {showsCollection(options) && (
              <Field id="collection" label={t("admin.editor.collection")} error={errors.collection}>
                <select
                  id="collection"
                  value={form.collection}
                  onChange={(event) => update({ collection: event.target.value })}
                  className={fieldClass}
                  {...invalidProps("collection", errors.collection)}
                >
                  {options.collections.map((collection) => (
                    <option key={collection.slug} value={collection.slug}>
                      {collection.name}
                    </option>
                  ))}
                </select>
              </Field>
            )}
            {options.features.versions && options.versions.length > 0 && (
              <div className="flex flex-col gap-1.5 text-sm font-semibold">
                <span>{t("admin.editor.version")}</span>
                <div className="md:max-w-[480px]">
                  <Segmented
                    label={t("admin.editor.version")}
                    value={form.version}
                    onChange={(version) => update({ version })}
                    options={[
                      { value: null, label: t("admin.editor.noVersion") },
                      ...options.versions.map((version) => ({
                        value: version.slug as string | null,
                        label: version.name,
                      })),
                    ]}
                  />
                </div>
                <FieldError id="version-error" error={errors.version} />
              </div>
            )}
            {options.tags.length > 0 && (
              <div className="flex flex-col gap-1.5 text-sm font-semibold">
                <span id="tags-label">{t("admin.editor.tags")}</span>
                <div role="group" aria-labelledby="tags-label" className="flex flex-wrap gap-2">
                  {options.tags.map((tag) => {
                    const pressed = form.tags.includes(tag.slug);
                    return (
                      <button
                        key={tag.slug}
                        type="button"
                        aria-pressed={pressed}
                        onClick={() => toggleTag(tag.slug)}
                        className={cn(
                          "min-h-10 border px-3 text-[13px] font-semibold",
                          pressed
                            ? "border-primary bg-primary text-primary-contrast"
                            : "border-border bg-surface text-accent",
                        )}
                      >
                        {tag.name}
                      </button>
                    );
                  })}
                </div>
                <FieldError id="tags-error" error={errors.tags} />
              </div>
            )}
            <Field
              id="description"
              label={t("admin.editor.description")}
              hint={t("admin.editor.descriptionHint")}
              error={errors.description}
            >
              <textarea
                id="description"
                rows={4}
                value={form.description}
                onChange={(event) => update({ description: event.target.value })}
                maxLength={5000}
                className="w-full resize-y border border-border bg-surface px-3 py-2.5 text-base font-normal text-text focus-visible:border-accent focus-visible:outline-2 focus-visible:outline-primary aria-invalid:border-error"
                {...invalidProps("description", errors.description)}
              />
            </Field>
          </Card>

          <Card title={t("admin.editor.availability")}>
            {(options.features.on_order || form.saleMode === "on_order") && (
              <div className="md:max-w-[420px]">
                <Segmented
                  strong
                  label={t("admin.editor.saleMode")}
                  value={form.saleMode}
                  onChange={(saleMode) => update({ saleMode })}
                  options={SALE_MODES.map((mode) => ({
                    value: mode,
                    label: t(`admin.editor.saleMode.${mode}`),
                  }))}
                />
              </div>
            )}
            {form.saleMode === "on_order" ? (
              <p data-on-order-hint="" className="text-sm leading-snug text-muted">
                {range
                  ? t("admin.editor.onOrderHint", range)
                  : t("admin.editor.onOrderHintNoSizes")}
              </p>
            ) : !form.category ? (
              <Hint>{t("admin.editor.noCategoryForSizes")}</Hint>
            ) : (
              <>
                <Hint>{t("admin.editor.stockHint")}</Hint>
                <SizeGrid sizes={sizes} onToggle={toggleSize} />
              </>
            )}
            <FieldError id="sizes-error" error={errors.sizes ?? errors.sale_mode} />
          </Card>
        </div>

        <div className="flex flex-col gap-3 md:sticky md:top-6 md:w-[340px] md:shrink-0 md:gap-4">
          <Card title={t("admin.editor.price")}>
            <div className="flex flex-col gap-1.5">
              <label
                className={cn(
                  "flex h-14 items-center gap-1.5 border-2 border-accent bg-surface px-3 text-[22px] font-bold text-accent md:h-13",
                  errors.price && "border-error",
                )}
              >
                <span aria-hidden="true">{symbol}</span>
                <input
                  id="price"
                  inputMode={priceFormat.decimals > 0 ? "decimal" : "numeric"}
                  value={form.price}
                  onChange={(event) => update({ price: event.target.value })}
                  aria-label={t("admin.editor.price")}
                  placeholder="0"
                  className="w-full min-w-0 bg-transparent font-bold outline-none"
                  {...invalidProps("price", errors.price)}
                />
              </label>
              <FieldError id="price-error" error={errors.price} />
            </div>
          </Card>

          <div className="fixed inset-x-0 bottom-0 z-10 flex flex-col gap-2 border-t border-border bg-surface px-4 pt-3 pb-5 shadow-[0_-4px_16px_rgb(0_0_0/0.08)] md:static md:border-0 md:bg-transparent md:p-0 md:shadow-none">
            <Button type="submit" variant="outline" size="lg" disabled={status.kind === "saving"}>
              {status.kind === "saving"
                ? t("admin.editor.saving")
                : t(isDraft ? "admin.editor.saveDraft" : "admin.editor.save")}
            </Button>
            <p
              role="status"
              className={cn(
                "min-h-5 text-center text-sm font-semibold",
                status.kind === "invalid" || status.kind === "error" ? "text-error" : "text-muted",
              )}
            >
              {statusText}
            </p>
          </div>
          {!product && <Hint>{t("admin.editor.codeHint")}</Hint>}
        </div>
      </div>
    </form>
  );
}
