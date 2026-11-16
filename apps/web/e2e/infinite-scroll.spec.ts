import { expect, test, type Page } from "@playwright/test";

import { cardCodes, cards, loadMoreButton, pageSizeOf, withoutAutoLoad } from "./listing-pages";

// Scroll infinito y vuelta al listado, en celular y escritorio. No conocen los
// datos: usan la sección con más productos y comparan con la API. Necesitan más
// de una página: correr `make dev` con LISTING_PAGE_SIZE=3 (ver make e2e).

type ApiListing = { items: { code: string }[]; total: number };

const SECTIONS = [
  { path: "/stock", section: "stock" },
  { path: "/encargue", section: "on_order" },
];

/** La sección con más productos y todos sus códigos en el orden de la API. */
async function biggestSection(page: Page) {
  const listings = await Promise.all(
    SECTIONS.map(async ({ path, section }) => {
      const response = await page.request.get(`/api/products?section=${section}&limit=100`);
      expect(response.ok()).toBe(true);
      const listing = (await response.json()) as ApiListing;
      return { path, codes: listing.items.map((p) => p.code) };
    }),
  );
  return listings.reduce((a, b) => (b.codes.length > a.codes.length ? b : a));
}

/** Abre la sección y salta el test si no tiene al menos dos páginas. */
async function openWithPages(page: Page, path: string, total: number) {
  await page.goto(path);
  await expect(page.getByTestId("products")).toBeVisible();
  const size = await pageSizeOf(page);
  test.skip(total <= size, `Hace falta más de una página: correr make dev con LISTING_PAGE_SIZE=3`);
  return size;
}

function pagesParam(loaded: number, size: number): RegExp {
  const pages = Math.ceil(loaded / size);
  return pages > 1 ? new RegExp(`[?&]paginas=${pages}(&|$)`) : /^[^?]*$/;
}

/** Baja hasta el final una y otra vez hasta tener todos los productos. */
async function scrollToTheEnd(page: Page, total: number) {
  await expect(async () => {
    await cards(page).last().scrollIntoViewIfNeeded();
    await page.mouse.wheel(0, 2000);
    await expect(cards(page)).toHaveCount(total, { timeout: 1000 });
  }).toPass();
}

test("al bajar se suman páginas hasta el final y la URL dice cuántas", async ({ page }) => {
  const { path, codes } = await biggestSection(page);
  const size = await openWithPages(page, path, codes.length);

  await scrollToTheEnd(page, codes.length);

  expect(await cardCodes(page)).toEqual(codes);
  await expect(page).toHaveURL(pagesParam(codes.length, size));
  await expect(loadMoreButton(page)).toBeHidden();
});

test("«Ver más» suma una página cuando la carga automática no anda", async ({ page }) => {
  await withoutAutoLoad(page);
  const { path, codes } = await biggestSection(page);
  const size = await openWithPages(page, path, codes.length);
  await expect(cards(page)).toHaveCount(size);

  await loadMoreButton(page).click();

  const loaded = Math.min(2 * size, codes.length);
  await expect(cards(page)).toHaveCount(loaded);
  expect(await cardCodes(page)).toEqual(codes.slice(0, loaded));
  await expect(page).toHaveURL(/[?&]paginas=2(&|$)/);
});

test("una URL con paginas trae esas páginas del servidor", async ({ page }) => {
  await withoutAutoLoad(page);
  const { path, codes } = await biggestSection(page);
  const size = await openWithPages(page, path, codes.length);

  await page.goto(`${path}?paginas=2`);

  const loaded = Math.min(2 * size, codes.length);
  await expect(cards(page)).toHaveCount(loaded);
  expect(await cardCodes(page)).toEqual(codes.slice(0, loaded));
});

test("al volver del detalle están los mismos productos en la misma posición", async ({ page }) => {
  const { path, codes } = await biggestSection(page);
  await openWithPages(page, path, codes.length);
  await scrollToTheEnd(page, codes.length);
  const url = page.url();
  const last = cards(page).last();
  await last.scrollIntoViewIfNeeded();
  const scrollY = await page.evaluate(() => window.scrollY);

  await last.getByRole("link").click();
  await expect(page).toHaveURL(/\/p\//);
  const refetched: string[] = [];
  page.on("request", (request) => {
    if (request.url().includes("/api/products")) refetched.push(request.url());
  });
  await page.goBack();

  await expect(page).toHaveURL(url);
  await expect(cards(page)).toHaveCount(codes.length);
  expect(await cardCodes(page)).toEqual(codes);
  await expect(cards(page).last()).toBeInViewport();
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBeCloseTo(scrollY, -1);
  // Lo cargado vuelve de la memoria del navegador, sin pedirlo de nuevo.
  expect(refetched).toEqual([]);
});
