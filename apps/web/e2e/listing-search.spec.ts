import { expect, test, type Page } from "@playwright/test";

import { cardCodes, cards, loadAll } from "./listing-pages";

type ApiListing = {
  items: { code: string; name: string }[];
  facets: { categories: { value: string; name: string; parent: string | null }[] };
};

// Búsqueda del listado en celular y escritorio. No conoce los datos del cliente:
// toma un producto de la API, lo busca con la caja y compara con la API.

async function apiListing(page: Page, query: string): Promise<ApiListing> {
  const response = await page.request.get(`/api/products?${query}&limit=100`);
  expect(response.ok()).toBe(true);
  return (await response.json()) as ApiListing;
}

async function search(page: Page, text: string) {
  const box = page.getByRole("searchbox", { name: "Buscar en esta sección" });
  await box.fill(text);
  await box.press("Enter");
}

test("buscar por código encuentra el producto y la URL lo refleja", async ({ page }) => {
  const [product] = (await apiListing(page, "section=stock")).items;
  test.skip(!product, "No hay productos en stock");

  const code = product.code.toLowerCase();

  await page.goto("/stock");
  await search(page, code);

  await expect(page).toHaveURL((url) => url.searchParams.get("q") === code);
  // Es por subcadena: otro código (o nombre) puede contenerlo. Se compara con la API.
  const expected = (await apiListing(page, `section=stock&q=${encodeURIComponent(code)}`)).items;
  const codes = expected.map((p) => p.code);
  expect(codes).toContain(product.code);
  await expect(cards(page).first()).toBeVisible();
  await loadAll(page);
  expect(await cardCodes(page)).toEqual(codes);

  // Recargar muestra lo mismo y la caja conserva el texto.
  await page.reload();
  await loadAll(page);
  expect(await cardCodes(page)).toEqual(codes);
  await expect(page.getByRole("searchbox")).toHaveValue(code);
});

test("buscar por nombre muestra lo mismo que la API, y los filtros conservan la búsqueda", async ({
  page,
}) => {
  const [product] = (await apiListing(page, "section=stock")).items;
  test.skip(!product, "No hay productos en stock");
  // La primera palabra del nombre, en mayúsculas: no distingue mayúsculas.
  const word = product.name.split(" ")[0].toUpperCase();

  await page.goto("/stock");
  await search(page, word);
  // Hasta que no navega, la grilla es la de antes (sin búsqueda).
  await expect(page).toHaveURL((url) => url.searchParams.get("q") === word);

  const expected = await apiListing(page, `section=stock&q=${encodeURIComponent(word)}`);
  expect(expected.items.map((p) => p.code)).toContain(product.code);
  await expect(cards(page).first()).toBeVisible();
  await loadAll(page);
  expect(await cardCodes(page)).toEqual(expected.items.map((p) => p.code));

  // Un filtro se cruza con la búsqueda y la deja en la URL.
  const category = expected.facets.categories.find((c) => c.parent === null);
  test.skip(!category, "La búsqueda no tiene categorías");
  await page
    .locator("[data-filter=category]")
    .getByRole("link", { name: category!.name, exact: true })
    .click();
  await expect(page).toHaveURL(/[?&]q=/);
  await expect(page).toHaveURL(new RegExp(`[?&]category=${category!.value}(&|$)`));

  // Borrar la búsqueda deja el filtro.
  await page.getByRole("link", { name: "Borrar búsqueda" }).click();
  await expect(page).not.toHaveURL(/[?&]q=/);
  await expect(page).toHaveURL(new RegExp(`[?&]category=${category!.value}(&|$)`));
  await expect(page.getByRole("searchbox")).toHaveValue("");
});

test("una búsqueda sin resultados lo dice", async ({ page }) => {
  await page.goto("/stock?q=zzzzqqqq");

  await expect(page.getByText("No encontramos productos para «zzzzqqqq».")).toBeVisible();
  await expect(cards(page)).toHaveCount(0);
});
