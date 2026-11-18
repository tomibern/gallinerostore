import { expect, test, type Page } from "@playwright/test";

import { formatPrice } from "../lib/money";

// Listado de productos del admin, en celular (tarjetas) y escritorio (tabla). No conoce
// los datos del cliente: compara lo que se ve con lo que devuelve la API, y reconoce
// estado, agotado y destacado por sus atributos. Entra con el admin de prueba que crea
// `make seed`.
const EMAIL = process.env.SEED_ADMIN_EMAIL ?? "admin@example.com";
const PASSWORD = process.env.SEED_ADMIN_PASSWORD ?? "admin-de-prueba";

type ApiStore = { locale: string; price_decimals: number };
type ApiItem = {
  code: string;
  name: string;
  price: number;
  currency: string;
  status: string;
  featured: boolean;
  availability: string;
  sizes: { label: string; status: string }[];
};
type ApiList = { items: ApiItem[]; has_more: boolean; total: number };

// Los filtros, con su texto del diccionario del núcleo.
const FILTERS = [
  ["all", "Todos"],
  ["stock", "En stock"],
  ["on_order", "Por encargue"],
  ["sold_out", "Agotados"],
  ["draft", "Borradores"],
  ["hidden", "Ocultos"],
  ["archived", "Archivados"],
] as const;

async function logIn(page: Page) {
  await page.goto("/admin/login?next=%2Fadmin%2Fproductos");
  await page.getByLabel("Email").fill(EMAIL);
  await page.getByLabel("Contraseña").fill(PASSWORD);
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page).toHaveURL(/\/admin\/productos$/);
}

async function apiList(page: Page, query: Record<string, string>): Promise<ApiList> {
  const params = new URLSearchParams({ limit: "20", ...query });
  const response = await page.request.get(`/api/admin/products?${params}`);
  expect(response.ok()).toBe(true);
  return (await response.json()) as ApiList;
}

// Las filas visibles: la tabla en escritorio o las tarjetas en el celular.
const rows = (page: Page) => page.locator("[data-code]:visible");

async function expectRows(page: Page, list: ApiList) {
  await expect(rows(page)).toHaveCount(list.items.length);
  await expect(
    rows(page).evaluateAll((els) => els.map((el) => (el as HTMLElement).dataset.code)),
  ).resolves.toEqual(list.items.map((item) => item.code));
}

function filterButton(page: Page, label: string) {
  return page.getByRole("group", { name: "Filtrar productos" }).getByRole("button", {
    name: label,
    exact: true,
  });
}

test.beforeEach(async ({ page }) => {
  await logIn(page);
});

test("muestra los productos que devuelve la API, con sus datos", async ({ page }) => {
  const store = (await (await page.request.get("/api/store")).json()) as ApiStore;
  const list = await apiList(page, {});
  expect(list.items.length).toBeGreaterThan(0);

  await expectRows(page, list);
  await expect(page.locator("[data-total]")).toHaveAttribute("data-total", String(list.total));
  await expect(filterButton(page, "Todos")).toHaveAttribute("aria-pressed", "true");

  for (const item of list.items) {
    const row = page.locator(`[data-code="${item.code}"]:visible`);
    await expect(row).toContainText(item.name);
    await expect(row).toContainText(item.code);
    await expect(row).toContainText(
      formatPrice(item.price, item.currency, store.locale, store.price_decimals),
    );
    await expect(row.locator("[data-status]")).toHaveAttribute("data-status", item.status);
    const soldOut = item.availability === "sold_out" || item.availability === "sold_out_on_order";
    await expect(row.locator("[data-sold-out]")).toHaveCount(soldOut ? 1 : 0);
    await expect(row).toHaveAttribute("data-featured", String(item.featured));
    // Cada fila lleva al editor del producto.
    await expect(row.getByRole("link").first()).toHaveAttribute(
      "href",
      `/admin/productos/${item.code.toLowerCase()}`,
    );
  }
});

test("en escritorio, los talles sin stock van tachados y la estrella marca los destacados", async ({
  page,
  isMobile,
}) => {
  test.skip(isMobile, "En el celular la tarjeta resume los talles.");
  const list = await apiList(page, {});
  await expectRows(page, list);

  for (const item of list.items) {
    const row = page.locator(`[data-code="${item.code}"]:visible`);
    await expect(
      row
        .locator("[data-size-status]")
        .evaluateAll((els) => els.map((el) => (el as HTMLElement).dataset.sizeStatus)),
    ).resolves.toEqual(item.sizes.map((size) => size.status));
    await expect(
      row.getByRole("img", { name: item.featured ? "Destacado" : "No destacado" }),
    ).toBeVisible();
  }
});

test("en el celular, la tarjeta resume los talles", async ({ page, isMobile }) => {
  test.skip(!isMobile, "En escritorio la tabla muestra cada talle.");
  const list = await apiList(page, {});
  await expectRows(page, list);

  for (const item of list.items) {
    const row = page.locator(`[data-code="${item.code}"]:visible`);
    const { sizes } = item;
    if (sizes.length === 0) continue;
    if (sizes.every((size) => size.status === "on_order")) {
      await expect(row).toContainText(sizes[0].label);
      await expect(row).toContainText(sizes[sizes.length - 1].label);
    } else {
      const available = sizes.filter((size) => size.status === "in_stock").length;
      await expect(row).toContainText(`${available}/${sizes.length}`);
    }
  }
});

test("cada filtro muestra lo mismo que la API y queda en la URL", async ({ page }) => {
  await expect(rows(page).first()).toBeVisible();

  for (const [filter, label] of FILTERS) {
    const list = await apiList(page, { filter });
    await filterButton(page, label).click();
    await expect(filterButton(page, label)).toHaveAttribute("aria-pressed", "true");
    if (filter !== "all") await expect(page).toHaveURL(/[?&]filtro=/);
    if (list.items.length === 0) {
      await expect(rows(page)).toHaveCount(0);
      await expect(page.getByRole("status")).toBeVisible();
    } else {
      await expectRows(page, list);
    }
  }
});

test("busca por código y por nombre", async ({ page }) => {
  const [first] = (await apiList(page, {})).items;

  const search = page.getByRole("searchbox", { name: "Buscar productos" });
  await search.fill(first.code.toLowerCase());
  await expect(page).toHaveURL(/[?&]q=/);
  await expectRows(page, await apiList(page, { q: first.code.toLowerCase() }));
  await expect(rows(page).first()).toHaveAttribute("data-code", first.code);

  // La búsqueda queda en la URL: una recarga la mantiene.
  await page.reload();
  await expect(search).toHaveValue(first.code.toLowerCase());
  await expectRows(page, await apiList(page, { q: first.code.toLowerCase() }));

  const word = first.name.split(" ")[0];
  await search.fill(word);
  await expect(page).toHaveURL(new RegExp(`[?&]q=${encodeURIComponent(word)}`));
  await expectRows(page, await apiList(page, { q: word }));
});

test("una búsqueda sin resultados lo dice", async ({ page }) => {
  await page.getByRole("searchbox", { name: "Buscar productos" }).fill("zzzz-no-existe-zzzz");

  await expect(page).toHaveURL(/[?&]q=zzzz-no-existe-zzzz/);
  await expect(rows(page)).toHaveCount(0);
  await expect(page.getByRole("status")).toContainText("zzzz-no-existe-zzzz");
});
