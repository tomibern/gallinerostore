import { expect, test, type Page } from "@playwright/test";

type ApiInquiry = { channel: "whatsapp" | "instagram"; message: string; url: string };
type ApiStore = { general_inquiries: ApiInquiry[] };

// Consulta general («¿Buscás algo que no está?»), en celular y escritorio. Como el
// resto de los e2e, no conoce los textos del cliente: compara cada recuadro con el
// mensaje y el link que arma la API, y lo encuentra por dónde está (`data-placement`).

const PLACEMENTS = [
  { path: "/stock", placement: "listing" },
  { path: "/encargue", placement: "listing" },
  { path: "/no-existe/tampoco", placement: "not-found" },
  { path: "/p/no-existe-tampoco", placement: "not-found" },
  { path: "/como-comprar", placement: "how-to-buy" },
  { path: "/", placement: "footer" },
];

async function generalInquiry(page: Page, channel: ApiInquiry["channel"]) {
  const response = await page.request.get("/api/store");
  expect(response.ok()).toBe(true);
  const { general_inquiries } = (await response.json()) as ApiStore;
  return general_inquiries.find((i) => i.channel === channel);
}

function block(page: Page, placement: string) {
  return page.locator(`[data-testid="general-inquiry"][data-placement="${placement}"]`);
}

for (const { path, placement } of PLACEMENTS) {
  test(`WhatsApp abre wa.me con la consulta general (${placement}, ${path})`, async ({ page }) => {
    const inquiry = await generalInquiry(page, "whatsapp");
    test.skip(!inquiry, "La tienda no tiene WhatsApp cargado.");

    await page.goto(path);

    const link = block(page, placement).locator('[data-channel="whatsapp"]');
    await link.scrollIntoViewIfNeeded();
    await expect(link).toBeVisible();
    await expect(link).toHaveAttribute("href", inquiry!.url);
    await expect(link).toHaveAttribute("target", "_blank");
    expect(new URL(inquiry!.url).searchParams.get("text")).toBe(inquiry!.message);
  });

  test(`Instagram abre la hoja con la consulta general (${placement}, ${path})`, async ({
    page,
  }) => {
    const inquiry = await generalInquiry(page, "instagram");
    test.skip(!inquiry, "La tienda no ofrece Instagram.");

    await page.goto(path);
    const button = block(page, placement).locator('[data-channel="instagram"]');
    await button.scrollIntoViewIfNeeded();
    await button.click();

    const sheet = page.getByRole("dialog");
    await expect(sheet).toBeVisible();
    await expect(sheet.getByTestId("inquiry-message")).toHaveValue(inquiry!.message);
    await expect(sheet.getByRole("link")).toHaveAttribute("href", inquiry!.url);

    await page.keyboard.press("Escape");
    await expect(sheet).toBeHidden();
  });
}

test("el pie del detalle lleva la consulta general sin repetir los botones del producto", async ({
  page,
}) => {
  const listing = await page.request.get("/api/products?section=stock&limit=1");
  const [product] = ((await listing.json()) as { items: { code: string }[] }).items;
  test.skip(!product, "No hay productos en stock.");

  await page.goto(`/p/${product.code.toLowerCase()}`);

  // Un solo bloque de botones del producto y la consulta general en el pie.
  await expect(page.getByTestId("inquiry-actions")).toHaveCount(1);
  await expect(block(page, "footer")).toHaveCount(1);
});
