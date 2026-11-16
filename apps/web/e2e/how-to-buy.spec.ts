import { expect, test, type Page } from "@playwright/test";

type ApiStore = {
  how_to_buy_md: string;
  faq: { question: string; answer_md: string }[];
};

// «Cómo comprar», en celular y escritorio. No conoce los textos del cliente: toma
// las preguntas de la API y busca cada una por su encabezado.

async function store(page: Page): Promise<ApiStore> {
  const response = await page.request.get("/api/store");
  expect(response.ok()).toBe(true);
  return (await response.json()) as ApiStore;
}

test("muestra el título y el contenido de «Cómo comprar»", async ({ page }) => {
  const { how_to_buy_md } = await store(page);

  const response = await page.goto("/como-comprar");

  expect(response?.status()).toBe(200);
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  // Cada título del Markdown («## …») es un encabezado de la página.
  for (const [, title] of how_to_buy_md.matchAll(/^## (.+)$/gm)) {
    await expect(page.getByRole("heading", { level: 2, name: title.trim() })).toBeVisible();
  }
});

test("las preguntas frecuentes se abren y se cierran de a una", async ({ page }) => {
  const { faq } = await store(page);
  test.skip(faq.length === 0, "La tienda no tiene preguntas frecuentes.");

  await page.goto("/como-comprar");
  const item = (question: string) =>
    page.getByRole("group").filter({ has: page.getByRole("heading", { name: question }) });

  // Todas cerradas al cargar.
  for (const { question } of faq) {
    await expect(item(question)).toHaveJSProperty("open", false);
  }

  const [first, second] = faq;
  await item(first.question).getByRole("heading", { name: first.question }).click();
  await expect(item(first.question)).toHaveJSProperty("open", true);
  await expect(item(first.question).getByTestId("faq-answer")).toBeVisible();

  if (second) {
    // Abrir otra cierra la anterior.
    await item(second.question).getByRole("heading", { name: second.question }).click();
    await expect(item(second.question)).toHaveJSProperty("open", true);
    await expect(item(first.question)).toHaveJSProperty("open", false);
    await expect(item(first.question).getByTestId("faq-answer")).toBeHidden();
  }

  const last = second ?? first;
  await item(last.question).getByRole("heading", { name: last.question }).click();
  await expect(item(last.question)).toHaveJSProperty("open", false);
});

test("«Cómo comprar» no se desborda a lo ancho en un celular de 360 px", async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 740 });
  await page.goto("/como-comprar");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();

  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow).toBe(0);
});
