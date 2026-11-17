import { expect, test, type BrowserContext, type Page } from "@playwright/test";

type ApiInquiry = { channel: "whatsapp" | "instagram" };
type ApiSize = { label: string; inquiries: ApiInquiry[] };
type ApiDetail = { code: string; sizes: ApiSize[] };
type SavedEvent = {
  type: string;
  product_code: string | null;
  channel: string | null;
  size: string | null;
  page: string | null;
  source: string | null;
  device: string | null;
};

// Eventos anónimos: una visita y una consulta quedan guardadas con lo que corresponde.
// Los verifica con el endpoint de e2e de la API, que solo existe con E2E_ENDPOINTS=true
// (LISTING_PAGE_SIZE=3 RATE_LIMIT_ENABLED=false E2E_ENDPOINTS=true make dev).
// En desarrollo React manda cada visita dos veces (Strict Mode): se cuenta «al menos una».

async function product(page: Page, channel: ApiInquiry["channel"]): Promise<ApiDetail | null> {
  const listing = await page.request.get("/api/products?section=stock");
  expect(listing.ok()).toBe(true);
  for (const { code } of ((await listing.json()) as { items: { code: string }[] }).items) {
    const detail = (await (
      await page.request.get(`/api/products/${code.toLowerCase()}`)
    ).json()) as ApiDetail;
    if (detail.sizes.some((s) => s.inquiries.some((i) => i.channel === channel))) return detail;
  }
  return null;
}

async function sessionId(page: Page): Promise<string> {
  await expect
    .poll(() => page.evaluate(() => sessionStorage.getItem("events.session")))
    .toMatch(/^[0-9a-f]{32}$/);
  return (await page.evaluate(() => sessionStorage.getItem("events.session")))!;
}

// Espera a que la sesión tenga un evento que cumpla con `expected`.
async function expectEvent(page: Page, expected: Partial<SavedEvent>) {
  const id = await sessionId(page);
  const response = await page.request.get(`/api/e2e/events?session_id=${id}`);
  test.skip(response.status() === 404, "La API no tiene los endpoints de e2e (E2E_ENDPOINTS).");
  await expect
    .poll(async () => {
      const events = (await (
        await page.request.get(`/api/e2e/events?session_id=${id}`)
      ).json()) as SavedEvent[];
      return events.filter((event) =>
        Object.entries(expected).every(([key, value]) => event[key as keyof SavedEvent] === value),
      ).length;
    })
    .toBeGreaterThanOrEqual(1);
}

async function events(page: Page): Promise<SavedEvent[]> {
  const id = await sessionId(page);
  return (await (
    await page.request.get(`/api/e2e/events?session_id=${id}`)
  ).json()) as SavedEvent[];
}

// Los chats no salen a internet: se responde vacío.
async function stubChats(context: BrowserContext) {
  await context.route(/^https:\/\/(wa|ig)\.me\//, (route) => route.fulfill({ body: "" }));
}

test("la visita al detalle y la consulta por WhatsApp quedan registradas", async ({
  page,
  context,
  isMobile,
}) => {
  const detail = await product(page, "whatsapp");
  test.skip(!detail, "No hay un producto en stock con WhatsApp.");
  const code = detail!.code;
  const size = detail!.sizes.at(-1)!;
  const device = isMobile ? "mobile" : "desktop";
  await stubChats(context);

  await page.goto(`/p/${code.toLowerCase()}?utm_source=E2E`);
  await expectEvent(page, { type: "product_view", product_code: code, source: "e2e", device });

  await page.locator(`label[data-size="${size.label}"]`).click();
  const popup = page.waitForEvent("popup");
  await page.getByTestId("inquiry-actions").locator('[data-channel="whatsapp"]').click();
  await popup;

  await expectEvent(page, {
    type: "contact_click",
    product_code: code,
    channel: "whatsapp",
    size: size.label,
    source: "e2e",
    device,
  });
});

test("abrir la hoja de Instagram no cuenta; tocar «Abrir Instagram» sí", async ({
  page,
  context,
}) => {
  const detail = await product(page, "instagram");
  test.skip(!detail, "La tienda no ofrece Instagram.");
  const size = detail!.sizes[0];
  await stubChats(context);

  await page.goto(`/p/${detail!.code.toLowerCase()}`);
  await expectEvent(page, { type: "product_view", product_code: detail!.code });
  await page.locator(`label[data-size="${size.label}"]`).click();
  await page.getByTestId("inquiry-actions").locator('[data-channel="instagram"]').click();
  const sheet = page.getByRole("dialog");
  await expect(sheet).toBeVisible();

  expect((await events(page)).filter((e) => e.type === "contact_click")).toEqual([]);

  const popup = page.waitForEvent("popup");
  await sheet.getByRole("link").click();
  await popup;
  await expectEvent(page, {
    type: "contact_click",
    product_code: detail!.code,
    channel: "instagram",
    size: size.label,
  });
});

test("el origen de la entrada se guarda para toda la visita", async ({ page }) => {
  await page.goto("/?utm_source=historia");
  await expectEvent(page, { type: "page_view", page: "home", source: "historia" });

  // Navegación dentro del sitio: la URL ya no tiene utm, el origen sigue siendo el mismo.
  await page.goto("/como-comprar");
  await expectEvent(page, { type: "page_view", page: "how_to_buy", source: "historia" });
});

test("la consulta general registra el canal y la página", async ({ page, context }) => {
  const store = (await (await page.request.get("/api/store")).json()) as {
    general_inquiries: ApiInquiry[];
  };
  test.skip(
    !store.general_inquiries.some((i) => i.channel === "whatsapp"),
    "La tienda no tiene WhatsApp cargado.",
  );
  await stubChats(context);

  await page.goto("/stock");
  await expectEvent(page, { type: "page_view", page: "stock" });
  const link = page
    .locator('[data-testid="general-inquiry"][data-placement="listing"]')
    .locator('[data-channel="whatsapp"]');
  await link.scrollIntoViewIfNeeded();
  const popup = page.waitForEvent("popup");
  await link.click();
  await popup;

  await expectEvent(page, { type: "general_contact_click", channel: "whatsapp", page: "stock" });
});
