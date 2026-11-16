import { expect, test, type Page } from "@playwright/test";

type ApiProduct = { code: string; availability: string };
type ApiBlock = { key: string; slides: { full: string; alt: string }[] };

// Home en celular y escritorio. No conoce los datos del cliente: compara la
// página con lo que publica la API.
const MAX_FEATURED = 8;

async function apiFeatured(page: Page): Promise<ApiProduct[]> {
  const response = await page.request.get("/api/products?featured=true");
  expect(response.ok()).toBe(true);
  return ((await response.json()) as { items: ApiProduct[] }).items.slice(0, MAX_FEATURED);
}

/** El primer bloque con al menos 2 fotos, o null si la tienda no tiene ninguno. */
async function rotatingBlock(page: Page): Promise<ApiBlock | null> {
  const store = (await (await page.request.get("/api/store")).json()) as {
    home_blocks: ApiBlock[];
  };
  return store.home_blocks.find((block) => block.slides.length > 1) ?? null;
}

test("la home tiene la portada y los accesos a las dos secciones", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  const access = page.getByRole("main").getByRole("navigation");
  await expect(access.getByRole("link")).toHaveCount(2);
  await expect(access.locator('a[href="/stock"]')).toBeVisible();
  await expect(access.locator('a[href="/encargue"]')).toBeVisible();
});

test("los destacados son los de la API, en su orden y con su disponibilidad", async ({ page }) => {
  const featured = await apiFeatured(page);

  await page.goto("/");

  const cards = page.locator("[data-testid=featured] > li");
  if (featured.length === 0) {
    await expect(page.getByTestId("featured")).toHaveCount(0);
    return;
  }
  await expect(cards).toHaveCount(featured.length);
  await expect(cards.evaluateAll((items) => items.map((li) => li.dataset.code))).resolves.toEqual(
    featured.map((p) => p.code),
  );
  for (const product of featured) {
    await expect(
      page.locator(`[data-code="${product.code}"] [data-availability="${product.availability}"]`),
    ).toBeVisible();
  }
});

test("el carrusel pasa solo a la foto siguiente y se elige a mano", async ({ page }) => {
  await page.clock.install();
  const block = await rotatingBlock(page);
  test.skip(!block, "Ningún bloque de la home tiene 2 fotos o más");

  await page.goto("/");
  const carousel = page.getByTestId("home-carousel").first();
  const active = carousel.locator("[data-active]");
  await expect(active).toHaveAttribute("data-index", "0");
  await expect(active.getByRole("img", { includeHidden: true })).toHaveAttribute(
    "src",
    block!.slides[0].full,
  );

  await page.clock.runFor(4000);
  await expect(active).toHaveAttribute("data-index", "1");
  await expect(active.getByRole("img", { includeHidden: true })).toHaveAttribute(
    "src",
    block!.slides[1].full,
  );

  const last = block!.slides.length - 1;
  await carousel.getByRole("group").getByRole("button").nth(last).click();
  await expect(active).toHaveAttribute("data-index", String(last));
});

test("el botón detiene y reanuda la rotación", async ({ page }) => {
  await page.clock.install();
  test.skip(!(await rotatingBlock(page)), "Ningún bloque de la home tiene 2 fotos o más");

  await page.goto("/");
  const carousel = page.getByTestId("home-carousel").first();
  const active = carousel.locator("[data-active]");
  const rotation = carousel.getByTestId("carousel-rotation");

  await rotation.click();
  await page.mouse.move(0, 0);
  await page.clock.runFor(8000);
  await expect(active).toHaveAttribute("data-index", "0");

  await rotation.click();
  await page.mouse.move(0, 0);
  await page.clock.runFor(4000);
  await expect(active).toHaveAttribute("data-index", "1");
});

test("con «reducir movimiento» el carrusel arranca detenido", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.clock.install();
  test.skip(!(await rotatingBlock(page)), "Ningún bloque de la home tiene 2 fotos o más");

  await page.goto("/");
  const carousel = page.getByTestId("home-carousel").first();
  await expect(carousel.getByTestId("carousel-rotation")).toBeVisible();
  await page.clock.runFor(8000);
  await expect(carousel.locator("[data-active]")).toHaveAttribute("data-index", "0");
});
