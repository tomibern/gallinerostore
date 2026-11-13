import { expect, test, type Page } from "@playwright/test";

type FacetValue = { value: string; name: string; count: number };
type ApiListing = {
  items: { code: string }[];
  facets: Record<"versions" | "collections" | "tags" | "sizes", FacetValue[]> & {
    categories: (FacetValue & { parent: string | null })[];
  };
};

// Filtros y orden del listado en celular y escritorio. No conocen los datos del
// cliente: eligen valores de las facetas que publica la API y comparan la grilla
// con lo que devuelve la API para la misma query string.

async function apiListing(page: Page, query: string): Promise<ApiListing> {
  const response = await page.request.get(`/api/products?${query}`);
  expect(response.ok()).toBe(true);
  return (await response.json()) as ApiListing;
}

async function expectCards(page: Page, codes: string[]) {
  const cards = page.locator("[data-testid=products] > li");
  await expect(cards).toHaveCount(codes.length);
  await expect(cards.evaluateAll((items) => items.map((li) => li.dataset.code))).resolves.toEqual(
    codes,
  );
}

function chip(page: Page, filter: string, name: string) {
  return page.locator(`[data-filter=${filter}]`).getByRole("link", { name, exact: true });
}

test("filtrar por categoría muestra lo mismo que la API y queda en la URL", async ({ page }) => {
  const { facets } = await apiListing(page, "section=stock");
  const category = facets.categories[0];
  test.skip(!category, "Los datos cargados no tienen categorías en stock");

  await page.goto("/stock");
  await chip(page, "category", category.name).click();

  await expect(page).toHaveURL(new RegExp(`[?&]category=${category.value}(&|$)`));
  const expected = await apiListing(page, `section=stock&category=${category.value}`);
  expect(expected.items.length).toBe(category.count);
  await expectCards(
    page,
    expected.items.map((p) => p.code),
  );
  await expect(chip(page, "category", category.name)).toHaveAttribute("aria-current", "true");

  // Recargar muestra el mismo listado: todo vive en la URL.
  await page.reload();
  await expectCards(
    page,
    expected.items.map((p) => p.code),
  );
});

test("dos valores de un filtro se suman y otro filtro los cruza", async ({ page }) => {
  const { facets } = await apiListing(page, "section=stock");
  const [first, second] = facets.categories.filter((c) => c.parent === null);
  test.skip(!second, "Hacen falta dos categorías de nivel 1 en stock");

  await page.goto("/stock");
  await chip(page, "category", first.name).click();
  await expect(chip(page, "category", first.name)).toHaveAttribute("aria-current", "true");
  await chip(page, "category", second.name).click();
  await expect(chip(page, "category", second.name)).toHaveAttribute("aria-current", "true");

  const both = await apiListing(
    page,
    `section=stock&category=${first.value}&category=${second.value}`,
  );
  expect(both.items.length).toBe(first.count + second.count);
  await expectCards(
    page,
    both.items.map((p) => p.code),
  );

  // Un talle (o etiqueta) cruza la selección.
  const crossing = both.facets.sizes[0] ?? both.facets.tags[0];
  test.skip(!crossing, "No hay talles ni etiquetas para cruzar");
  const filter = both.facets.sizes[0] ? "size" : "tag";
  await chip(page, filter, crossing.name).click();
  await expect(chip(page, filter, crossing.name)).toHaveAttribute("aria-current", "true");

  const crossed = await apiListing(
    page,
    `section=stock&category=${first.value}&category=${second.value}&${filter}=${encodeURIComponent(crossing.value)}`,
  );
  expect(crossed.items.length).toBe(crossing.count);
  await expectCards(
    page,
    crossed.items.map((p) => p.code),
  );
});

for (const [sort, label] of [
  ["newest", "Más nuevos"],
  ["price_asc", "Menor precio"],
  ["price_desc", "Mayor precio"],
] as const) {
  test(`ordenar por ${label} sigue el orden de la API`, async ({ page }) => {
    await page.goto("/encargue");
    await page
      .getByRole("group", { name: "Ordenar por" })
      .getByRole("link", { name: label })
      .click();

    await expect(page).toHaveURL(new RegExp(`[?&]sort=${sort}`));
    const expected = await apiListing(page, `section=on_order&sort=${sort}`);
    await expectCards(
      page,
      expected.items.map((p) => p.code),
    );

    await page.reload();
    await expectCards(
      page,
      expected.items.map((p) => p.code),
    );
  });
}

test("ordenar mantiene los filtros elegidos", async ({ page }) => {
  const { facets } = await apiListing(page, "section=on_order");
  const category = facets.categories[0];
  test.skip(!category, "Los datos cargados no tienen encargues");

  await page.goto(`/encargue?category=${category.value}`);
  await page
    .getByRole("group", { name: "Ordenar por" })
    .getByRole("link", { name: "Mayor precio" })
    .click();

  await expect(page).toHaveURL(new RegExp(`category=${category.value}.*sort=price_desc`));
  const expected = await apiListing(
    page,
    `section=on_order&category=${category.value}&sort=price_desc`,
  );
  await expectCards(
    page,
    expected.items.map((p) => p.code),
  );
});

test("Por encargue no tiene filtro de talle", async ({ page }) => {
  await page.goto("/encargue");
  await expect(page.getByRole("complementary", { name: "Filtros" })).toBeVisible();
  await expect(page.locator("[data-filter=size]")).toHaveCount(0);
});

test("sin resultados muestra un estado vacío y deja limpiar los filtros", async ({ page }) => {
  await page.goto("/stock?category=no-existe");

  await expect(page.getByText("No hay productos con estos filtros.")).toBeVisible();
  await expect(page.getByTestId("products")).toHaveCount(0);

  await page.getByRole("link", { name: "Limpiar filtros" }).click();
  await expect(page).toHaveURL(/\/stock$/);
  const all = await apiListing(page, "section=stock");
  await expectCards(
    page,
    all.items.map((p) => p.code),
  );
});

test("los filtros van arriba en el celular y en una barra lateral en escritorio", async ({
  page,
  isMobile,
}) => {
  await page.goto("/stock");
  const filters = await page.getByRole("complementary", { name: "Filtros" }).boundingBox();
  const grid = await page.getByTestId("products").boundingBox();
  expect(filters && grid).toBeTruthy();

  if (isMobile) {
    expect(filters!.y + filters!.height).toBeLessThanOrEqual(grid!.y);
  } else {
    expect(filters!.x + filters!.width).toBeLessThanOrEqual(grid!.x);
    expect(filters!.y).toBeLessThan(grid!.y + grid!.height);
  }
});
