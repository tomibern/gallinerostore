import { expect, test } from "@playwright/test";

import { formatPrice } from "../lib/money";

type ApiStore = { locale: string; price_decimals: number };

type ApiProduct = {
  code: string;
  name: string;
  price: number;
  currency: string;
  section: string;
  availability: string;
  cover: { thumb: string } | null;
};

// Las secciones En stock y Por encargue en celular y escritorio. No conocen los
// datos del cliente: comparan cada página con lo que publica la API.
const SECTIONS = [
  { path: "/stock", section: "stock" },
  { path: "/encargue", section: "on_order" },
];

for (const { path, section } of SECTIONS) {
  test(`${path} muestra las tarjetas de la sección en el orden de la API`, async ({ page }) => {
    const response = await page.request.get(`/api/products?section=${section}`);
    expect(response.ok()).toBe(true);
    const products = (await response.json()) as ApiProduct[];
    expect(products.length).toBeGreaterThan(0);
    const store = (await (await page.request.get("/api/store")).json()) as ApiStore;

    await page.goto(path);

    const cards = page.locator("[data-testid=products] > li");
    await expect(cards).toHaveCount(products.length);
    await expect(cards.evaluateAll((items) => items.map((li) => li.dataset.code))).resolves.toEqual(
      products.map((p) => p.code),
    );

    for (const product of products) {
      const card = page.locator(`[data-code="${product.code}"]`);
      await expect(card.getByRole("heading", { name: product.name })).toBeVisible();
      await expect(card).toContainText(
        formatPrice(product.price, product.currency, store.locale, store.price_decimals),
      );
      await expect(card.locator(`[data-availability="${product.availability}"]`)).toBeVisible();
      await expect(card.getByRole("link")).toHaveAttribute(
        "href",
        `/p/${product.code.toLowerCase()}`,
      );

      expect(product.cover, `${product.code} sin portada`).not.toBeNull();
      const image = card.getByRole("img");
      await expect(image).toHaveAttribute("src", product.cover!.thumb);
      await image.scrollIntoViewIfNeeded();
      await expect
        .poll(() => image.evaluate((img: HTMLImageElement) => img.complete && img.naturalWidth))
        .toBeGreaterThan(0);
    }
  });
}

test("la grilla tiene 2 columnas en el celular y 3 o más en escritorio", async ({
  page,
  isMobile,
}) => {
  await page.goto("/stock");
  const grid = page.getByTestId("products");
  await expect(grid).toBeVisible();

  const columns = await grid.evaluate(
    (el) => getComputedStyle(el).gridTemplateColumns.split(" ").length,
  );
  if (isMobile) expect(columns).toBe(2);
  else expect(columns).toBeGreaterThanOrEqual(3);
});

test("un agotado aparece en Por encargue y no en En stock", async ({ page }) => {
  const onOrder = (await (
    await page.request.get("/api/products?section=on_order")
  ).json()) as ApiProduct[];
  const soldOut = onOrder.find((p) => p.availability === "sold_out_on_order");
  test.skip(!soldOut, "Los datos cargados no tienen ningún agotado");

  await page.goto("/stock");
  await expect(page.getByTestId("products")).toBeVisible();
  await expect(page.locator(`[data-code="${soldOut!.code}"]`)).toHaveCount(0);

  await page.goto("/encargue");
  await expect(
    page.locator(`[data-code="${soldOut!.code}"] [data-availability="sold_out_on_order"]`),
  ).toBeVisible();
});
