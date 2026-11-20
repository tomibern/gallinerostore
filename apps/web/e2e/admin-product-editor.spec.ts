import { expect, test, type Page } from "@playwright/test";

import { formatPrice, parsePrice } from "../lib/money";

// Editor de producto del admin, en celular y escritorio: crear un borrador, editarlo y
// verlo actualizado en el listado. No conoce los datos del cliente: elige la primera
// categoría y compara precios con el formato de la tienda. Entra con el admin de prueba
// que crea `make seed`. Cada corrida deja su borrador (todavía no se pueden borrar).
const EMAIL = process.env.SEED_ADMIN_EMAIL ?? "admin@example.com";
const PASSWORD = process.env.SEED_ADMIN_PASSWORD ?? "admin-de-prueba";

type ApiStore = { locale: string; currency: string; price_decimals: number };

async function logIn(page: Page) {
  await page.goto("/admin/login?next=%2Fadmin%2Fproductos");
  await page.getByLabel("Email").fill(EMAIL);
  await page.getByLabel("Contraseña").fill(PASSWORD);
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page).toHaveURL(/\/admin\/productos$/);
}

async function store(page: Page): Promise<ApiStore> {
  const response = await page.request.get("/api/store");
  expect(response.ok()).toBe(true);
  return (await response.json()) as ApiStore;
}

test("crear un borrador, editarlo y verlo actualizado en el listado", async ({ page }, info) => {
  const name = `Producto e2e ${info.project.name} ${Date.now()}`;
  const { locale, currency, price_decimals } = await store(page);
  const shown = (typed: string) =>
    formatPrice(
      parsePrice(typed, currency, locale, price_decimals)!,
      currency,
      locale,
      price_decimals,
    );

  await logIn(page);
  await page.getByRole("link", { name: "+ Nuevo producto" }).click();
  await expect(page).toHaveURL(/\/admin\/productos\/nuevo$/);

  // Sin nombre ni categoría, la API marca los dos campos.
  await page.getByRole("button", { name: "Guardar borrador" }).click();
  await expect(page.getByText("Revisá los campos marcados.")).toBeVisible();
  await expect(page.getByLabel("Nombre")).toHaveAttribute("aria-invalid", "true");
  await expect(page.getByLabel("Categoría")).toHaveAttribute("aria-invalid", "true");

  // Crear: el código lo asigna la API y la URL pasa a ser la del producto.
  await page.getByLabel("Nombre").fill(name);
  await page.getByLabel("Categoría").selectOption({ index: 1 });
  await page.getByLabel("Precio").fill("45000");
  await page.getByRole("button", { name: "Guardar borrador" }).click();
  await expect(page.getByRole("status").filter({ hasText: "Guardado." })).toBeVisible();
  await expect(page).toHaveURL(/\/admin\/productos\/[a-z0-9]+-\d+$/);
  const code = await page.locator("[data-product-code]").getAttribute("data-product-code");
  expect(code).toBeTruthy();
  expect(page.url()).toContain(`/admin/productos/${code!.toLowerCase()}`);

  // Un producto de stock arranca con todos los talles disponibles; uno pasa a sin stock.
  const sizes = page.locator("[data-size]");
  await expect(sizes.first()).toHaveAttribute("aria-pressed", "true");
  await sizes.first().click();
  await expect(sizes.first()).toHaveAttribute("aria-pressed", "false");

  // Editar y guardar.
  await page.getByLabel("Nombre").fill(`${name} editado`);
  await page.getByLabel("Precio").fill("52000");
  await page.getByRole("button", { name: "Guardar borrador" }).click();
  await expect(page.getByRole("status").filter({ hasText: "Guardado." })).toBeVisible();

  // Al recargar sigue igual: lo guardó la API.
  await page.reload();
  await expect(page.getByLabel("Nombre")).toHaveValue(`${name} editado`);
  await expect(page.getByLabel("Precio")).toHaveValue(/^52\D?000/);
  await expect(page.locator("[data-size]").first()).toHaveAttribute("aria-pressed", "false");

  // Pasar a encargue: no hay grilla de talles, solo el texto.
  await page.getByRole("radio", { name: "Por encargue" }).click();
  await expect(page.locator("[data-size]")).toHaveCount(0);
  await expect(page.locator("[data-on-order-hint]")).toBeVisible();
  await page.getByRole("button", { name: "Guardar borrador" }).click();
  await expect(page.getByRole("status").filter({ hasText: "Guardado." })).toBeVisible();

  // En el listado del admin, entre los borradores, con el nombre y el precio nuevos.
  await page.goto(`/admin/productos?q=${encodeURIComponent(code!)}&filtro=borradores`);
  const row = page.locator(`[data-code="${code}"]:visible`);
  await expect(row).toHaveCount(1);
  await expect(row).toContainText(`${name} editado`);
  await expect(row).toContainText(shown("52000"));
  await expect(row.locator("[data-status]")).toHaveAttribute("data-status", "draft");
});
