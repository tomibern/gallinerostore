// Lo que el editor de producto del admin arma a partir de las opciones y del producto
// que devuelve la API. Las reglas (código, talles al cambiar de modo o de grupo) son de
// la API; acá solo se prepara el formulario y se eligen los textos. Sin imports del
// servidor.

import type { ValidationError } from "@catalog/api-client";

import type { AdminProduct, AdminProductPatch, CatalogOptions, SaleMode } from "./admin-api";
import type { FieldErrors } from "./admin-settings";
import { parsePrice, priceInput } from "./money";
import { t } from "./texts";

export type PriceFormat = { currency: string; locale: string; decimals: number };

/** Un talle del formulario: disponible o sin stock. */
export type SizeChoice = { label: string; inStock: boolean };

export type ProductForm = {
  name: string;
  category: string;
  collection: string;
  version: string | null;
  season: string;
  tags: string[];
  description: string;
  price: string;
  saleMode: SaleMode;
  sizes: SizeChoice[];
};

/** El formulario de un producto nuevo: de stock, en la colección por defecto. */
export function emptyForm(options: CatalogOptions): ProductForm {
  return {
    name: "",
    category: "",
    collection: options.default_collection ?? options.collections[0]?.slug ?? "",
    version: null,
    season: "",
    tags: [],
    description: "",
    price: "",
    saleMode: "stock",
    sizes: [],
  };
}

/** El formulario con lo que tiene guardado un producto. */
export function productForm(product: AdminProduct, format: PriceFormat): ProductForm {
  return {
    name: product.name,
    category: product.category,
    collection: product.collection,
    version: product.version,
    season: product.season ?? "",
    tags: product.tags,
    description: product.description ?? "",
    price: priceInput(product.price, format.currency, format.locale, format.decimals),
    saleMode: product.sale_mode,
    sizes: product.sizes.map((size) => ({ label: size.label, inStock: size.in_stock })),
  };
}

/** El grupo de talles de una categoría, o null si no hay categoría elegida. */
export function sizeGroup(options: CatalogOptions, category: string): string | null {
  return options.categories.find((option) => option.slug === category)?.size_group ?? null;
}

/**
 * Los talles que muestra la grilla de un producto de stock. Mientras el producto
 * guardado tenga filas de ese grupo, son las suyas; si recién pasa a stock o cambia de
 * grupo, se muestran todos los del grupo disponibles, como los va a dejar la API al
 * guardar. `choices` son los que tocó el admin.
 */
export function stockSizes(
  options: CatalogOptions,
  form: ProductForm,
  saved: AdminProduct | null,
): SizeChoice[] {
  const group = sizeGroup(options, form.category);
  if (!group) return [];
  const keepsRows =
    saved !== null && saved.sale_mode === "stock" && sizeGroup(options, saved.category) === group;
  const labels = keepsRows ? saved.sizes.map((size) => size.label) : (options.sizes[group] ?? []);
  const touched = new Map(form.sizes.map((size) => [size.label, size.inStock]));
  return labels.map((label) => ({ label, inStock: touched.get(label) ?? true }));
}

/** El primero y el último talle del grupo, para el texto de un encargue. */
export function groupRange(
  options: CatalogOptions,
  category: string,
): { first: string; last: string } | null {
  const group = sizeGroup(options, category);
  const labels = group ? (options.sizes[group] ?? []) : [];
  if (labels.length === 0) return null;
  return { first: labels[0], last: labels[labels.length - 1] };
}

/** Si el editor muestra el campo de colección: con la función activa y más de una. */
export function showsCollection(options: CatalogOptions): boolean {
  return options.features.collections && options.collections.length > 1;
}

/** Las categorías como se eligen: las hijas con su madre adelante («Abrigos › Buzos»). */
export function categoryLabels(options: CatalogOptions): { slug: string; label: string }[] {
  const names = new Map(options.categories.map((category) => [category.slug, category.name]));
  return options.categories.map((category) => ({
    slug: category.slug,
    label: category.parent
      ? t("admin.editor.categoryChild", {
          parent: names.get(category.parent) ?? category.parent,
          child: category.name,
        })
      : category.name,
  }));
}

/**
 * El cuerpo para la API, o el error del precio si no se puede leer. El precio se tipea
 * en la moneda y viaja en la unidad menor (ADR 0002); vacío es 0.
 */
export function productBody(
  form: ProductForm,
  sizes: SizeChoice[],
  options: CatalogOptions,
  format: PriceFormat,
): { body: AdminProductPatch & { name: string; category: string } } | { priceError: string } {
  const typed = form.price.trim();
  const price = typed ? parsePrice(typed, format.currency, format.locale, format.decimals) : 0;
  if (price === null) return { priceError: t("admin.editor.error.price") };
  return {
    body: {
      name: form.name,
      category: form.category,
      ...(showsCollection(options) && form.collection ? { collection: form.collection } : {}),
      // Con las versiones apagadas no se manda: guardar no borra la que tenga.
      ...(options.features.versions ? { version: form.version } : {}),
      season: form.season || null,
      tags: form.tags,
      description: form.description || null,
      price,
      sale_mode: form.saleMode,
      sizes:
        form.saleMode === "stock"
          ? sizes.map((size) => ({ label: size.label, in_stock: size.inStock }))
          : [],
    },
  };
}

/**
 * La clave del campo según el `loc` del error: `name`, `category`, `collection`,
 * `version`, `season`, `tags`, `description`, `price`, `sale_mode` o `sizes` (un error
 * de una etiqueta o de un talle se muestra en su grupo).
 */
export function productFieldKey(loc: ValidationError["loc"]): string {
  const path = loc.filter((part) => part !== "body");
  return String(path[0] ?? "");
}

function productMessage(error: ValidationError): string {
  const ctx = (error.ctx ?? {}) as Record<string, unknown>;
  switch (error.type) {
    case "missing":
    case "string_too_short":
      return t("admin.editor.error.required");
    case "string_too_long":
      return t("admin.editor.error.tooLong", { max: String(ctx.max_length ?? "") });
    case "unknown":
      return t("admin.editor.error.unknown");
    case "unknown_size":
      return t("admin.editor.error.unknownSize");
    case "on_order_with_sizes":
      return t("admin.editor.error.onOrderWithSizes");
    case "less_than_equal":
    case "greater_than_equal":
    case "int_parsing":
      return t("admin.editor.error.price");
    default:
      return t("admin.editor.error.invalid");
  }
}

/** Un error por campo (el primero que da la API). */
export function productFieldErrors(detail: ValidationError[]): FieldErrors {
  const errors: FieldErrors = {};
  for (const error of detail) {
    errors[productFieldKey(error.loc)] ??= productMessage(error);
  }
  return errors;
}
