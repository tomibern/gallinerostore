import { expect, test, type APIRequestContext } from "@playwright/test";

type StoryItem = {
  kind: "milestone" | "stat" | "fun_fact";
  year: number | null;
  title: string;
  body: string | null;
};
type ApiDetail = { code: string; story: StoryItem[] };

// Historia del producto en el detalle. No conoce los datos ni los textos del
// cliente: busca en la API un producto con historia y uno sin, y reconoce las
// tarjetas de los hitos por su estado accesible (aria-expanded), no por el texto.
// El seed tiene que traer los dos casos: si falta uno, el test falla.

async function publishedDetails(request: APIRequestContext): Promise<ApiDetail[]> {
  const details: ApiDetail[] = [];
  for (const section of ["stock", "on_order"]) {
    const listing = await request.get(`/api/products?section=${section}&limit=100`);
    expect(listing.ok()).toBe(true);
    const items = ((await listing.json()) as { items: { code: string }[] }).items;
    for (const { code } of items) {
      const response = await request.get(`/api/products/${code.toLowerCase()}`);
      expect(response.ok()).toBe(true);
      details.push((await response.json()) as ApiDetail);
    }
  }
  return details;
}

test("muestra la historia en un producto que la tiene y no en uno sin", async ({ page }) => {
  const details = await publishedDetails(page.request);
  const withStory = details.find((d) => d.story.some((item) => item.kind === "milestone"));
  const withoutStory = details.find((d) => d.story.length === 0);
  expect(withStory, "un producto publicado con hitos en su historia").toBeDefined();
  expect(withoutStory, "un producto publicado sin historia").toBeDefined();

  await page.goto(`/p/${withoutStory!.code.toLowerCase()}`);
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await expect(page.getByTestId("product-story")).toHaveCount(0);

  await page.goto(`/p/${withStory!.code.toLowerCase()}`);
  const story = page.getByTestId("product-story");
  await expect(story).toBeVisible();
  const milestones = withStory!.story.filter((item) => item.kind === "milestone");
  await expect(story.locator("button[aria-expanded]")).toHaveCount(milestones.length);
  for (const item of withStory!.story.filter((i) => i.kind !== "milestone")) {
    await expect(story).toContainText(item.title);
  }
});

test("las tarjetas de los hitos se dan vuelta con clic o toque y con teclado", async ({ page }) => {
  const details = await publishedDetails(page.request);
  const withStory = details.find((d) => d.story.some((item) => item.kind === "milestone"));
  expect(withStory, "un producto publicado con hitos en su historia").toBeDefined();
  const milestone = withStory!.story.find((item) => item.kind === "milestone")!;

  await page.goto(`/p/${withStory!.code.toLowerCase()}`);
  const card = page
    .getByTestId("product-story")
    .getByRole("button", { name: `${milestone.year} · ${milestone.title}` });
  const back = page.locator(`#${await card.getAttribute("aria-controls")}`);
  await expect(card).toHaveAttribute("aria-expanded", "false");
  await expect(back).toHaveAttribute("aria-hidden", "true");

  // Clic (en celular, un toque emulado): se da vuelta y muestra la anécdota.
  await card.click();
  await expect(card).toHaveAttribute("aria-expanded", "true");
  await expect(back).not.toHaveAttribute("aria-hidden", "true");
  await expect(back).toContainText(milestone.body!);

  // Teclado: Enter la vuelve y Espacio la da vuelta otra vez.
  await card.focus();
  await page.keyboard.press("Enter");
  await expect(card).toHaveAttribute("aria-expanded", "false");
  await page.keyboard.press("Space");
  await expect(card).toHaveAttribute("aria-expanded", "true");
});
