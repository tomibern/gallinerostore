import { expect, test, type Browser, type Page } from "@playwright/test";

// Ranking de productos y cifras de 7 días del listado del admin: una consulta en la
// tienda se ve en las dos pantallas. Otros tests (y el otro proyecto) consultan al mismo
// tiempo, así que se compara contra lo de antes («al menos una más»), no contra un
// número fijo. Entra con el admin de prueba de `make seed`, como metrics.spec.ts.
const EMAIL = process.env.SEED_ADMIN_EMAIL ?? "admin@example.com";
const PASSWORD = process.env.SEED_ADMIN_PASSWORD ?? "admin-de-prueba";

type ApiSize = { label: string; inquiries: { channel: string }[] };
type ApiDetail = { code: string; sizes: ApiSize[] };
type ApiRanking = { items: { code: string; inquiries: number }[] };
type ApiList = { items: { code: string; inquiries_7d: number }[] };

async function logIn(page: Page) {
  await page.goto("/admin/login");
  await page.getByLabel("Email").fill(EMAIL);
  await page.getByLabel("Contraseña").fill(PASSWORD);
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page).toHaveURL(/\/admin\/productos$/);
}

/** Un producto en stock que se consulta por WhatsApp, con el talle para hacerlo. */
async function productWithWhatsapp(page: Page): Promise<{ code: string; size: string } | null> {
  const listing = await page.request.get("/api/products?section=stock");
  expect(listing.ok()).toBe(true);
  for (const { code } of ((await listing.json()) as { items: { code: string }[] }).items) {
    const detail = (await (
      await page.request.get(`/api/products/${code.toLowerCase()}`)
    ).json()) as ApiDetail;
    const size = detail.sizes.find((s) => s.inquiries.some((i) => i.channel === "whatsapp"));
    if (size) return { code, size: size.label };
  }
  return null;
}

/** Las consultas del producto en el ranking de 7 días y en su fila del listado. */
async function inquiries(page: Page, code: string): Promise<{ ranking: number; list: number }> {
  const ranking = await page.request.get("/api/admin/metrics/products?period=7d");
  const list = await page.request.get(`/api/admin/products?q=${code}`);
  expect(ranking.ok() && list.ok()).toBe(true);
  const ranked = ((await ranking.json()) as ApiRanking).items.find((i) => i.code === code);
  const row = ((await list.json()) as ApiList).items.find((i) => i.code === code);
  return { ranking: ranked?.inquiries ?? 0, list: row?.inquiries_7d ?? 0 };
}

/** Un visitante (otro navegador, sin sesión) consulta el producto por WhatsApp. */
async function visitorAsks(browser: Browser, code: string, size: string) {
  const context = await browser.newContext();
  // Los chats no salen a internet: se responde vacío.
  await context.route(/^https:\/\/(wa|ig)\.me\//, (route) => route.fulfill({ body: "" }));
  const page = await context.newPage();
  await page.goto(`/p/${code.toLowerCase()}`);
  await page.locator(`label[data-size="${size}"]`).click();
  const recorded = page.waitForResponse(
    (response) =>
      response.url().endsWith("/api/events") &&
      response.request().postDataJSON()?.type === "contact_click",
  );
  const popup = page.waitForEvent("popup");
  await page.getByTestId("inquiry-actions").locator('[data-channel="whatsapp"]').click();
  await popup;
  expect((await recorded).status()).toBe(204);
  await context.close();
}

function count(text: string): number {
  return Number(text.replace(/\D/g, ""));
}

test("consultar un producto en la tienda lo suma al ranking y a su fila del listado", async ({
  page,
  browser,
  isMobile,
}) => {
  await logIn(page);
  const product = await productWithWhatsapp(page);
  test.skip(!product, "No hay un producto en stock con WhatsApp.");
  const { code, size } = product!;
  const before = await inquiries(page, code);

  await visitorAsks(browser, code, size);

  // Ranking: la fila del producto, con al menos una consulta más que antes.
  await page.goto("/admin/metricas");
  const ranked = page
    .getByRole("region", { name: "Ranking de productos" })
    .locator(`tr[data-code="${code}"]`);
  await expect(ranked).toBeVisible();
  expect(count(await ranked.locator('[data-column="inquiries"]').innerText())).toBeGreaterThan(
    before.ranking,
  );

  // Ordenar por visitas: la columna activa cambia y el producto sigue en el ranking.
  await page.getByRole("button", { name: "Ordenar por Visitas" }).click();
  await expect(page.getByRole("columnheader", { name: "Ordenar por Visitas" })).toHaveAttribute(
    "aria-sort",
    "descending",
  );
  await expect(ranked).toBeVisible();

  // Listado: en escritorio, la fila muestra las consultas de 7 días; en el celular, no.
  await page.goto(`/admin/productos?q=${code}`);
  const row = page.locator(`tr[data-code="${code}"]`);
  const cell = row.locator('[data-column="inquiries_7d"]');
  if (isMobile) {
    await expect(page.locator(`li[data-code="${code}"]`)).toBeVisible();
    await expect(cell).toBeHidden();
  } else {
    await expect(cell).toBeVisible();
    expect(count(await cell.innerText())).toBeGreaterThan(before.list);
    await expect(row.locator('[data-column="visits_7d"]')).toBeVisible();
  }
});
