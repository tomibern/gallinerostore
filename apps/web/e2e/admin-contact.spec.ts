import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

// Contacto y mensajes prearmados del panel. Entra con el admin de prueba de `make seed`
// (SEED_ADMIN_EMAIL y SEED_ADMIN_PASSWORD; por defecto, los del archivo de ejemplo de
// variables de entorno). Los textos del panel son del diccionario del núcleo; los datos
// del cliente se leen de la API.
const EMAIL = process.env.SEED_ADMIN_EMAIL ?? "admin@example.com";
const PASSWORD = process.env.SEED_ADMIN_PASSWORD ?? "admin-de-prueba";
const CSRF = { "X-Requested-With": "fetch" };

type ApiSize = {
  label: string;
  status: "in_stock" | "out_of_stock" | "on_order";
  inquiries: { channel: string; url: string }[];
};
type ApiDetail = { code: string; sizes: ApiSize[] };
type Settings = Record<string, unknown> & { message_variables?: unknown };

async function logIn(page: Page) {
  await page.goto("/admin/login?next=%2Fadmin%2Fcontenido");
  await page.getByLabel("Email").fill(EMAIL);
  await page.getByLabel("Contraseña").fill(PASSWORD);
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page).toHaveURL(/\/admin\/contenido$/);
}

/** Lo que se guarda, a partir de lo que devuelve GET /admin/settings. */
function toBody(settings: Settings) {
  const body = { ...settings };
  delete body.message_variables;
  return body;
}

/** Un producto publicado con un talle en stock y WhatsApp, si lo hay. */
async function inStockProduct(request: APIRequestContext) {
  const listing = await request.get("/api/products?section=stock");
  expect(listing.ok()).toBe(true);
  for (const { code } of ((await listing.json()) as { items: { code: string }[] }).items) {
    const detail = (await (
      await request.get(`/api/products/${code.toLowerCase()}`)
    ).json()) as ApiDetail;
    const size = detail.sizes.find(
      (s) => s.status === "in_stock" && s.inquiries.some((i) => i.channel === "whatsapp"),
    );
    if (size) return { code: detail.code, size };
  }
  return undefined;
}

// Cambia la configuración de la tienda: corre en un solo proyecto, así escritorio y
// celular no se pisan la plantilla al correr en paralelo.
test("cambiar la plantilla de talle disponible cambia el link de WhatsApp del detalle", async ({
  page,
}, testInfo) => {
  test.skip(testInfo.project.name !== "escritorio", "Cambia datos compartidos: un solo proyecto.");
  const sample = await inStockProduct(page.request);
  test.skip(!sample, "No hay un talle en stock con WhatsApp cargado.");

  await logIn(page);
  const original = (await (await page.request.get("/api/admin/settings")).json()) as Settings;
  const marker = `e2e-${Date.now()}`;

  try {
    const template = page.getByLabel("Talle disponible", { exact: true });
    await template.fill(`Consulta ${marker}: `);
    await page.getByRole("button", { name: "Insertar Talle en «Talle disponible»" }).click();
    await expect(template).toHaveValue(`Consulta ${marker}: {size}`);
    await page.getByRole("button", { name: "Guardar", exact: true }).click();
    await expect(page.getByRole("status").filter({ hasText: "Guardado" })).toBeVisible();

    await page.goto(`/p/${sample!.code.toLowerCase()}`);
    await page.locator(`label[data-size="${sample!.size.label}"]`).click();
    const whatsapp = page.getByTestId("inquiry-actions").locator('[data-channel="whatsapp"]');
    await expect(whatsapp).toHaveAttribute("href", /^https:\/\/wa\.me\//);
    const href = await whatsapp.getAttribute("href");
    expect(new URL(href!).searchParams.get("text")).toBe(
      `Consulta ${marker}: ${sample!.size.label}`,
    );
  } finally {
    // La base queda como estaba.
    const restored = await page.request.put("/api/admin/settings", {
      data: toBody(original),
      headers: CSRF,
    });
    expect(restored.ok()).toBe(true);
  }
});

test("un WhatsApp inválido muestra el error en su campo y no se guarda", async ({ page }) => {
  await logIn(page);
  const contact = async () =>
    ((await (await page.request.get("/api/admin/settings")).json()) as Settings).contact_channels;
  const before = await contact();

  await page.getByLabel("WhatsApp", { exact: true }).fill("123");
  await page.getByRole("button", { name: "Guardar", exact: true }).click();

  await expect(
    page.getByText("Tiene que ser un número con el código del país: entre 8 y 15 dígitos."),
  ).toBeVisible();
  await expect(page.getByLabel("WhatsApp", { exact: true })).toHaveAttribute(
    "aria-invalid",
    "true",
  );
  // Solo el contacto: la otra prueba puede estar guardando una plantilla al mismo tiempo.
  expect(await contact()).toEqual(before);
});

test("la vista previa muestra el mensaje armado por la API con un producto real", async ({
  page,
}) => {
  await logIn(page);
  const template = page.getByLabel("Talle disponible", { exact: true });
  await template.fill("Vista {code}");

  await page.getByRole("button", { name: "Vista previa · Talle disponible" }).click();

  await expect(page.getByRole("status").filter({ hasText: /^Con / })).toContainText(/Vista \S+/);
  // Solo vista previa: no se guardó.
  await page.reload();
  await expect(page.getByLabel("Talle disponible", { exact: true })).not.toHaveValue(
    "Vista {code}",
  );
});
