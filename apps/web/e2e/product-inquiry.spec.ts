import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

type ApiInquiry = { channel: "whatsapp" | "instagram"; message: string; url: string };
type ApiSize = {
  label: string;
  status: "in_stock" | "out_of_stock" | "on_order";
  inquiries: ApiInquiry[];
};
type ApiDetail = { code: string; name: string; sizes: ApiSize[] };

// Consulta desde el detalle, en celular y escritorio. Como el resto de los e2e, no
// conoce los datos ni los textos del cliente: compara la página con lo que publica
// la API (mensaje y link ya armados por talle y canal) y reconoce el caso por su
// atributo, no por el texto.

async function details(request: APIRequestContext): Promise<ApiDetail[]> {
  const codes: string[] = [];
  for (const section of ["stock", "on_order"]) {
    const listing = await request.get(`/api/products?section=${section}`);
    expect(listing.ok()).toBe(true);
    codes.push(
      ...((await listing.json()) as { items: { code: string }[] }).items.map((i) => i.code),
    );
  }
  return Promise.all(
    codes.map(async (code) => {
      const response = await request.get(`/api/products/${code.toLowerCase()}`);
      expect(response.ok()).toBe(true);
      return (await response.json()) as ApiDetail;
    }),
  );
}

async function find(
  request: APIRequestContext,
  matches: (product: ApiDetail) => boolean,
): Promise<ApiDetail | undefined> {
  return (await details(request)).find(matches);
}

const hasChannel = (channel: ApiInquiry["channel"]) => (product: ApiDetail) =>
  product.sizes.some((size) => size.inquiries.some((i) => i.channel === channel));

async function choose(page: Page, size: ApiSize) {
  // El radio está oculto detrás del botón con estilo: se hace clic en su etiqueta.
  await page.locator(`label[data-size="${size.label}"]`).click();
  await expect(page.getByTestId("size-status")).toHaveAttribute("data-status", size.status);
}

function inquiry(size: ApiSize, channel: ApiInquiry["channel"]): ApiInquiry {
  return size.inquiries.find((i) => i.channel === channel)!;
}

function actions(page: Page) {
  return page.getByTestId("inquiry-actions");
}

test("los botones se activan al elegir talle y el caso cambia según el talle", async ({ page }) => {
  // Un producto con varios talles y de más de un estado, si lo hay.
  const product =
    (await find(
      page.request,
      (p) => hasChannel("whatsapp")(p) && new Set(p.sizes.map((s) => s.status)).size > 1,
    )) ?? (await find(page.request, (p) => hasChannel("whatsapp")(p) && p.sizes.length > 1));
  test.skip(!product, "No hay un producto con varios talles y canales cargados.");

  await page.goto(`/p/${product!.code.toLowerCase()}`);
  const whatsapp = actions(page).locator('[data-channel="whatsapp"]');
  await expect(whatsapp).toBeDisabled();
  await expect(page.getByTestId("inquiry-action")).toHaveAttribute("data-status", "");

  for (const size of product!.sizes) {
    await choose(page, size);
    await expect(page.getByTestId("inquiry-action")).toHaveAttribute("data-status", size.status);
    await expect(whatsapp).toHaveAttribute("href", inquiry(size, "whatsapp").url);
  }
});

test("WhatsApp abre wa.me con el mensaje del talle, que lleva al mismo producto", async ({
  page,
}) => {
  const product = await find(page.request, hasChannel("whatsapp"));
  test.skip(!product, "La tienda no tiene WhatsApp cargado.");
  const size = product!.sizes.at(-1)!;
  const { message, url } = inquiry(size, "whatsapp");

  await page.goto(`/p/${product!.code.toLowerCase()}`);
  await choose(page, size);

  const link = actions(page).locator('[data-channel="whatsapp"]');
  await expect(link).toHaveAttribute("href", url);
  await expect(link).toHaveAttribute("target", "_blank");
  expect(url.startsWith("https://wa.me/")).toBe(true);
  expect(new URL(url).searchParams.get("text")).toBe(message);

  // El link del mensaje (el último del texto) abre este mismo producto.
  const productLink = message.match(/https?:\/\/\S+/g)!.at(-1)!;
  await page.goto(new URL(productLink).pathname);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(product!.name);
});

test.describe("Instagram", () => {
  test.use({ permissions: ["clipboard-read", "clipboard-write"] });

  test("la hoja muestra el mensaje, copia solo al tocar «Copiar mensaje» y abre Instagram", async ({
    page,
  }) => {
    const product = await find(page.request, hasChannel("instagram"));
    test.skip(!product, "La tienda no ofrece Instagram.");
    const size = product!.sizes[0];
    const { message, url } = inquiry(size, "instagram");

    await page.goto(`/p/${product!.code.toLowerCase()}`);
    await choose(page, size);
    const secure = await page.evaluate(() => window.isSecureContext);
    if (secure) await page.evaluate(() => navigator.clipboard.writeText("centinela"));

    await actions(page).locator('[data-channel="instagram"]').click();

    const sheet = page.getByRole("dialog");
    await expect(sheet).toBeVisible();
    await expect(sheet.getByTestId("inquiry-message")).toHaveValue(message);
    await expect(sheet.getByRole("link")).toHaveAttribute("href", url);
    expect(url.startsWith("https://ig.me/m/")).toBe(true);
    // Abrir la hoja no copia nada.
    if (secure) {
      expect(await page.evaluate(() => navigator.clipboard.readText())).toBe("centinela");
    }

    await sheet.getByTestId("copy-message").click();

    if (secure) {
      await expect(sheet.locator("[data-copy]")).toHaveAttribute("data-copy", "copied");
      expect(await page.evaluate(() => navigator.clipboard.readText())).toBe(message);
    } else {
      // Sin contexto seguro (por IP en la red) no hay portapapeles: el texto queda
      // seleccionado para copiarlo a mano.
      await expect(sheet.locator("[data-copy]")).toHaveAttribute("data-copy", "failed");
      const selected = await sheet
        .getByTestId("inquiry-message")
        .evaluate((el: HTMLTextAreaElement) => el.value.slice(el.selectionStart, el.selectionEnd));
      expect(selected).toBe(message);
    }

    await page.keyboard.press("Escape");
    await expect(sheet).toBeHidden();
  });
});

test("en el celular los botones quedan fijos abajo; en escritorio, en su lugar", async ({
  page,
  isMobile,
}) => {
  const product = await find(page.request, (p) => p.sizes.some((s) => s.inquiries.length > 0));
  test.skip(!product, "La tienda no tiene canales cargados.");

  await page.goto(`/p/${product!.code.toLowerCase()}`);
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));

  const bar = actions(page);
  const position = await bar.evaluate((el) => getComputedStyle(el).position);
  if (isMobile) {
    expect(position).toBe("fixed");
    const box = (await bar.boundingBox())!;
    const viewport = page.viewportSize()!;
    expect(Math.round(box.y + box.height)).toBeLessThanOrEqual(viewport.height);
    // El pie no queda tapado: lo último de la página se ve encima de la barra.
    const footer = (await page.locator("footer").last().boundingBox())!;
    expect(footer.y + footer.height).toBeLessThanOrEqual(box.y + 1);
  } else {
    expect(position).toBe("static");
  }
});

test("con talle único, los botones vienen activos sin elegir nada", async ({ page }) => {
  const product = await find(
    page.request,
    (p) => p.sizes.length === 1 && p.sizes[0].inquiries.length > 0,
  );
  test.skip(!product, "No hay un producto de talle único.");
  const [size] = product!.sizes;

  await page.goto(`/p/${product!.code.toLowerCase()}`);

  await expect(page.getByTestId("inquiry-action")).toHaveAttribute("data-status", size.status);
  for (const { channel } of size.inquiries) {
    await expect(actions(page).locator(`[data-channel="${channel}"]`)).toBeEnabled();
  }
});
