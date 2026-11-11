import { expect, test } from "@playwright/test";

type ApiProduct = { code: string; name: string; cover: { thumb: string } | null };

// El recorrido completo: navegador → Next → API → base, y fotos → Next → bucket.
// No conoce los datos del cliente: compara la página con lo que publica la API.
test("la página muestra los productos publicados con su foto cargada", async ({
  page,
  request,
}) => {
  const response = await request.get("/api/products");
  expect(response.ok()).toBe(true);
  const products = (await response.json()) as ApiProduct[];
  expect(products.length).toBeGreaterThan(0);

  await page.goto("/");

  const cards = page.locator("[data-testid=products] > li");
  await expect(cards).toHaveCount(products.length);

  for (const product of products) {
    const card = page.locator(`[data-code="${product.code}"]`);
    await expect(card.getByRole("heading", { name: product.name })).toBeVisible();

    expect(product.cover, `${product.code} sin portada`).not.toBeNull();
    const image = card.getByRole("img");
    await expect(image).toHaveAttribute("src", product.cover!.thumb);
    await image.scrollIntoViewIfNeeded();
    await expect
      .poll(() => image.evaluate((img: HTMLImageElement) => img.complete && img.naturalWidth))
      .toBeGreaterThan(0);
  }
});
