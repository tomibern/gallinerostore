import { expect, test, type Browser, type Page } from "@playwright/test";

// Métricas: las visitas de la tienda se ven en el panel, salvo las del admin con su sesión.
// Cada visita entra con un utm_source único, así el test reconoce la suya aunque otros
// tests (o el otro proyecto) sumen visitas al mismo tiempo. Entra con el admin de prueba
// de `make seed`, como admin-login.spec.ts.
const EMAIL = process.env.SEED_ADMIN_EMAIL ?? "admin@example.com";
const PASSWORD = process.env.SEED_ADMIN_PASSWORD ?? "admin-de-prueba";

function uniqueSource(prefix: string): string {
  return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

/** Entra a la tienda con ese origen y espera a que la API reciba la visita. */
async function visitStore(page: Page, source: string) {
  const recorded = page.waitForResponse(
    (response) => response.url().endsWith("/api/events") && response.request().method() === "POST",
  );
  await page.goto(`/?utm_source=${source}`);
  expect((await recorded).status()).toBe(204);
}

async function logIn(page: Page) {
  await page.goto("/admin/login");
  await page.getByLabel("Email").fill(EMAIL);
  await page.getByLabel("Contraseña").fill(PASSWORD);
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page).toHaveURL(/\/admin\/productos$/);
}

function sources(page: Page) {
  return page.getByRole("heading", { name: "De dónde llegan" }).locator("..");
}

/** El número de visitas de los últimos 7 días que muestra la pantalla. */
async function visits(page: Page): Promise<number> {
  await page.goto("/admin/metricas");
  // La tarjeta dice «Visitas», el número y la comparación, en ese orden.
  const [, value] = (await page.getByRole("group", { name: "Visitas" }).innerText()).split("\n");
  return Number(value.replace(/\D/g, ""));
}

async function visitorVisit(browser: Browser, source: string) {
  const visitor = await browser.newContext();
  await visitStore(await visitor.newPage(), source);
  await visitor.close();
}

test("una visita sin sesión se ve en Métricas", async ({ page, browser }) => {
  await logIn(page);
  const before = await visits(page);
  const source = uniqueSource("e2e-visita");

  await visitorVisit(browser, source);

  await page.goto("/admin/metricas");
  await expect(sources(page).getByText(source, { exact: true })).toBeVisible();
  expect(await visits(page)).toBeGreaterThan(before);
});

test("las visitas del admin con su sesión no cuentan", async ({ page, browser }) => {
  await logIn(page);
  const adminSource = uniqueSource("e2e-admin");
  const visitorSource = uniqueSource("e2e-visita");

  await visitStore(page, adminSource);
  // Una visita de otro navegador después: cuando se ve, la del admin ya se procesó.
  await visitorVisit(browser, visitorSource);

  await page.goto("/admin/metricas");
  await expect(sources(page).getByText(visitorSource, { exact: true })).toBeVisible();
  await expect(sources(page).getByText(adminSource, { exact: true })).toHaveCount(0);
});

test("el período se elige con las pestañas", async ({ page }) => {
  await logIn(page);
  await page.goto("/admin/metricas");

  const today = page.getByRole("tab", { name: "Hoy" });
  await today.click();

  await expect(today).toHaveAttribute("aria-selected", "true");
  await expect(page.getByRole("heading", { name: /Visitas y consultas · hoy/i })).toBeVisible();
  await expect(page.getByText("La web mide interés, no ventas", { exact: false })).toBeVisible();
});
