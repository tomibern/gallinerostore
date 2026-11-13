import { expect, test, type Page } from "@playwright/test";

type ApiStore = { name: string };

// El layout de la tienda en celular y escritorio. No conoce los datos ni los
// textos del cliente: toma el nombre de la API y busca los links por su ruta.
const NAV_LINKS = ["/stock", "/encargue", "/como-comprar"];

async function storeName(page: Page): Promise<string> {
  const response = await page.request.get("/api/store");
  expect(response.ok()).toBe(true);
  return ((await response.json()) as ApiStore).name;
}

test("la home muestra el encabezado y el pie de la tienda", async ({ page, isMobile }) => {
  const name = await storeName(page);
  await page.goto("/");

  const header = page.getByRole("banner");
  await expect(header).toBeVisible();
  const homeLink = header.getByRole("link", { name, exact: true });
  await expect(homeLink).toHaveAttribute("href", "/");

  // El logo es decorativo (alt vacío): el nombre de la tienda está al lado.
  const logo = header.locator("img").first();
  await expect
    .poll(() => logo.evaluate((img: HTMLImageElement) => img.complete && img.naturalWidth))
    .toBeGreaterThan(0);

  // En celular la navegación está detrás del botón de menú.
  if (isMobile) await header.getByRole("button", { expanded: false }).click();
  const nav = header.getByRole("navigation");
  for (const href of NAV_LINKS) {
    await expect(nav.locator(`a[href="${href}"]`)).toBeVisible();
  }

  const footer = page.getByRole("contentinfo");
  await footer.scrollIntoViewIfNeeded();
  await expect(footer).toBeVisible();
  await expect(footer.getByText(name).first()).toBeVisible();
  for (const href of NAV_LINKS) {
    await expect(footer.locator(`a[href="${href}"]`)).toBeVisible();
  }
});

test("la home no se desborda a lo ancho en un celular de 360 px", async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 740 });
  await page.goto("/");
  await expect(page.getByRole("banner")).toBeVisible();

  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow).toBe(0);
});
