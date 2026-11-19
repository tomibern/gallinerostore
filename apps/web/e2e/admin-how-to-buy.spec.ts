import { expect, test, type Page } from "@playwright/test";

// «Cómo comprar» y preguntas frecuentes del panel: lo que guarda el admin se ve en la
// tienda. Entra con el admin de prueba de `make seed` (SEED_ADMIN_EMAIL y
// SEED_ADMIN_PASSWORD; por defecto, los del archivo de ejemplo de variables de entorno).
// No conoce los textos del cliente: los lee de la API.
const EMAIL = process.env.SEED_ADMIN_EMAIL ?? "admin@example.com";
const PASSWORD = process.env.SEED_ADMIN_PASSWORD ?? "admin-de-prueba";
const CSRF = { "X-Requested-With": "fetch" };

type Content = {
  topics: { title: string; text: string }[];
  faq: { question: string; answer: string }[];
};

async function logIn(page: Page) {
  await page.goto("/admin/login?next=%2Fadmin%2Fcontenido");
  await page.getByLabel("Email").fill(EMAIL);
  await page.getByLabel("Contraseña").fill(PASSWORD);
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page).toHaveURL(/\/admin\/contenido$/);
}

// Cambia la configuración de la tienda: corre en un solo proyecto, así escritorio y
// celular no se pisan los textos al correr en paralelo.
test("editar un tema y agregar una pregunta se ve en «Cómo comprar»", async ({
  page,
}, testInfo) => {
  test.skip(testInfo.project.name !== "escritorio", "Cambia datos compartidos: un solo proyecto.");
  await logIn(page);
  const response = await page.request.get("/api/admin/settings/how-to-buy");
  expect(response.ok()).toBe(true);
  const original = (await response.json()) as Content;
  test.skip(original.topics.length === 0, "La tienda no tiene temas en «Cómo comprar».");
  const marker = `e2e-${Date.now()}`;

  try {
    const form = page.getByRole("form", { name: "Cómo comprar" });
    const topic = form.getByRole("group", { name: "Tema 1" });
    await topic.getByLabel("Título", { exact: true }).fill(`Tema ${marker}`);
    await topic.getByLabel("Texto", { exact: true }).fill(`Texto ${marker}.`);

    await form.getByRole("button", { name: "Agregar pregunta" }).click();
    const question = form.getByRole("group", { name: `Pregunta ${original.faq.length + 1}` });
    await expect(question.getByLabel("Pregunta", { exact: true })).toBeFocused();
    await question.getByLabel("Pregunta", { exact: true }).fill(`¿Pregunta ${marker}?`);
    await question.getByLabel("Respuesta", { exact: true }).fill(`Respuesta ${marker}.`);

    await form.getByRole("button", { name: "Guardar «Cómo comprar»" }).click();
    await expect(form.getByRole("status")).toHaveText(/Guardado/);

    await page.goto("/como-comprar");
    await expect(page.getByRole("heading", { level: 2, name: `Tema ${marker}` })).toBeVisible();
    await expect(page.getByText(`Texto ${marker}.`)).toBeVisible();
    const faq = page
      .getByRole("group")
      .filter({ has: page.getByRole("heading", { name: `¿Pregunta ${marker}?` }) });
    await faq.getByText(`¿Pregunta ${marker}?`).click();
    await expect(faq.getByText(`Respuesta ${marker}.`)).toBeVisible();
    // El admin nunca ve la estructura: la tienda tampoco muestra los «##».
    await expect(page.getByText("##")).toHaveCount(0);
  } finally {
    // La base queda como estaba.
    const restored = await page.request.put("/api/admin/settings/how-to-buy", {
      data: original,
      headers: CSRF,
    });
    expect(restored.ok()).toBe(true);
  }
});

test("un título vacío muestra el error en su campo y no se guarda", async ({ page }) => {
  await logIn(page);
  const content = async () =>
    (await (await page.request.get("/api/admin/settings/how-to-buy")).json()) as Content;
  const before = await content();

  const form = page.getByRole("form", { name: "Cómo comprar" });
  await form.getByRole("button", { name: "Agregar tema" }).click();
  const added = form.getByRole("group", { name: `Tema ${before.topics.length + 1}` });
  await added.getByLabel("Texto", { exact: true }).fill("Sin título.");
  await form.getByRole("button", { name: "Guardar «Cómo comprar»" }).click();

  await expect(added.getByText("No puede quedar vacío.")).toBeVisible();
  await expect(added.getByLabel("Título", { exact: true })).toHaveAttribute("aria-invalid", "true");
  // Lo que no se guardó no está (la otra prueba puede estar guardando al mismo tiempo).
  expect((await content()).topics.map((topic) => topic.text)).not.toContain("Sin título.");
});
