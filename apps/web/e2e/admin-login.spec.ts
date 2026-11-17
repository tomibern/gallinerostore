import { expect, test, type Page } from "@playwright/test";

// Login del admin y esqueleto del panel, en celular y escritorio. Entra con el admin de
// prueba que crea `make seed` (SEED_ADMIN_EMAIL y SEED_ADMIN_PASSWORD; por defecto, los
// del archivo de ejemplo de variables de entorno).
const EMAIL = process.env.SEED_ADMIN_EMAIL ?? "admin@example.com";
const PASSWORD = process.env.SEED_ADMIN_PASSWORD ?? "admin-de-prueba";

async function logIn(page: Page, password = PASSWORD) {
  await page.getByLabel("Email").fill(EMAIL);
  await page.getByLabel("Contraseña").fill(password);
  await page.getByRole("button", { name: "Entrar" }).click();
}

test("sin sesión, el panel lleva al login y después vuelve a la página pedida", async ({
  page,
}) => {
  await page.goto("/admin/metricas");

  await expect(page).toHaveURL(/\/admin\/login\?next=%2Fadmin%2Fmetricas$/);
  await logIn(page);

  await expect(page).toHaveURL(/\/admin\/metricas$/);
  const nav = page.getByRole("navigation", { name: "Secciones del panel" });
  await expect(nav.getByRole("link", { name: /Métricas/ })).toHaveAttribute("aria-current", "page");
  await expect(nav.getByRole("link", { name: /Productos/ })).toBeVisible();
  await expect(nav.getByRole("link", { name: /Contenido/ })).toBeVisible();
});

test("una contraseña incorrecta muestra el error y no entra", async ({ page }) => {
  await page.goto("/admin/login");

  await logIn(page, "no-es-esta-clave");

  await expect(page.locator("form").getByRole("alert")).toHaveText(
    "Email o contraseña incorrectos.",
  );
  await expect(page).toHaveURL(/\/admin\/login/);
});

test("cerrar sesión vuelve al login y el panel ya no se abre", async ({ page }) => {
  await page.goto("/admin");
  await logIn(page);
  await expect(page).toHaveURL(/\/admin\/productos$/);

  // En el celular, cerrar sesión está en Contenido y ajustes (Cuenta).
  await page.goto("/admin/contenido");
  await expect(page.getByText(`Entraste como ${EMAIL}.`)).toBeVisible();
  await page.getByRole("main").getByRole("button", { name: "Cerrar sesión" }).click();

  await expect(page).toHaveURL(/\/admin\/login$/);
  await page.goto("/admin/productos");
  await expect(page).toHaveURL(/\/admin\/login/);
});

test("el panel no se indexa", async ({ page }) => {
  await page.goto("/admin/login");

  await expect(page.locator('meta[name="robots"]')).toHaveAttribute("content", /noindex/);
});
