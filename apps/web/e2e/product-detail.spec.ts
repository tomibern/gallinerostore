import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

import { formatPrice } from "../lib/money";

type ApiStore = { locale: string; price_decimals: number };
type ApiSize = { label: string; status: "in_stock" | "out_of_stock" | "on_order" };
type ApiDetail = {
  code: string;
  name: string;
  price: number;
  currency: string;
  section: string;
  images: { full: string }[];
  sizes: ApiSize[];
};

// El detalle del producto en celular y escritorio. No conoce los datos ni los
// textos del cliente: compara la página con lo que publica la API y reconoce el
// estado de cada talle por su atributo, no por el texto.

async function details(request: APIRequestContext, section: string): Promise<ApiDetail[]> {
  const listing = await request.get(`/api/products?section=${section}`);
  expect(listing.ok()).toBe(true);
  const items = ((await listing.json()) as { items: { code: string }[] }).items;
  return Promise.all(
    items.map(async ({ code }) => {
      const response = await request.get(`/api/products/${code.toLowerCase()}`);
      expect(response.ok()).toBe(true);
      return (await response.json()) as ApiDetail;
    }),
  );
}

function sizePicker(page: Page) {
  return page.getByRole("group").filter({ has: page.getByRole("radio") });
}

async function expectSizesInOrder(page: Page, product: ApiDetail) {
  const radios = sizePicker(page).getByRole("radio");
  await expect(radios).toHaveCount(product.sizes.length);
  await expect(
    radios.evaluateAll((els) => els.map((el) => el.getAttribute("value"))),
  ).resolves.toEqual(product.sizes.map((s) => s.label));
}

async function choose(page: Page, size: ApiSize) {
  // El radio está oculto detrás del botón con estilo: se hace clic en su etiqueta.
  await sizePicker(page).locator(`label[data-size="${size.label}"]`).click();
  await expect(sizePicker(page).locator(`input[value="${size.label}"]`)).toBeChecked();
  const status = page.getByTestId("size-status");
  await expect(status).toHaveAttribute("data-status", size.status);
  await expect(status).toContainText(size.label);
}

test("abre un producto desde el listado y muestra sus datos y fotos", async ({ page }) => {
  const store = (await (await page.request.get("/api/store")).json()) as ApiStore;
  await page.goto("/stock");
  const card = page.locator("[data-testid=products] > li").first();
  const code = (await card.getAttribute("data-code"))!;

  await card.getByRole("link").click();

  await expect(page).toHaveURL(`/p/${code.toLowerCase()}`);
  const product = (await (
    await page.request.get(`/api/products/${code.toLowerCase()}`)
  ).json()) as ApiDetail;
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(product.name);
  await expect(page.getByRole("main")).toContainText(
    formatPrice(product.price, product.currency, store.locale, store.price_decimals),
  );
  const photos = page.getByTestId("gallery").locator("li img");
  await expect(photos).toHaveCount(product.images.length);
  await expect(photos.first()).toHaveAttribute("src", product.images[0].full);
  await expectSizesInOrder(page, product);
});

test("con varias fotos, las miniaturas muestran cada foto", async ({ page }) => {
  const all = [
    ...(await details(page.request, "stock")),
    ...(await details(page.request, "on_order")),
  ];
  const product = all.find((p) => p.images.length > 1);
  test.skip(!product, "Los datos cargados no tienen productos con varias fotos");

  await page.goto(`/p/${product!.code.toLowerCase()}`);
  const last = product!.images.length - 1;
  await page.getByTestId("gallery-thumbs").getByRole("button").nth(last).click();

  const photo = page.getByTestId("gallery").locator("li").nth(last);
  await expect(photo).toBeInViewport({ ratio: 0.9 });
});

test("en stock, elegir un talle sin stock lo marca y lo avisa", async ({ page }) => {
  const product = (await details(page.request, "stock")).find(
    (p) =>
      p.sizes.some((s) => s.status === "out_of_stock") &&
      p.sizes.some((s) => s.status === "in_stock"),
  );
  test.skip(!product, "Los datos cargados no tienen talles sin stock en En stock");

  await page.goto(`/p/${product!.code.toLowerCase()}`);
  await expectSizesInOrder(page, product!);

  await choose(
    page,
    product!.sizes.find((s) => s.status === "out_of_stock")!,
  );
  await choose(
    page,
    product!.sizes.find((s) => s.status === "in_stock")!,
  );
});

test("un encargue o un agotado ofrece los talles del grupo y muestra el aviso", async ({
  page,
}) => {
  const products = (await details(page.request, "on_order")).filter((p) => p.sizes.length > 1);
  test.skip(products.length === 0, "Los datos cargados no tienen encargues con varios talles");

  for (const product of products.slice(0, 2)) {
    await page.goto(`/p/${product.code.toLowerCase()}`);
    await expect(page.getByTestId("on-order-notice")).toBeVisible();
    await expectSizesInOrder(page, product);
    await choose(page, product.sizes.at(-1)!);
  }
});

test("con talle único, viene elegido", async ({ page }) => {
  const all = [
    ...(await details(page.request, "stock")),
    ...(await details(page.request, "on_order")),
  ];
  const product = all.find((p) => p.sizes.length === 1);
  test.skip(!product, "Los datos cargados no tienen productos de talle único");

  await page.goto(`/p/${product!.code.toLowerCase()}`);

  await expect(sizePicker(page).getByRole("radio")).toBeChecked();
  await expect(page.getByTestId("size-status")).toHaveAttribute(
    "data-status",
    product!.sizes[0].status,
  );
});

test("el código en mayúsculas redirige a la URL en minúsculas", async ({ page }) => {
  const [product] = await details(page.request, "stock");

  await page.goto(`/p/${product.code.toUpperCase()}`);

  await expect(page).toHaveURL(`/p/${product.code.toLowerCase()}`);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(product.name);
});
