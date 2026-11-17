import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

import { formatPrice } from "../lib/money";

type ApiStore = { name: string; locale: string; price_decimals: number };
type ApiImage = { full: string; width: number; height: number };
type ApiDetail = {
  code: string;
  name: string;
  price: number;
  currency: string;
  images: ApiImage[];
};
type ApiPage = { items: { code: string }[]; has_more: boolean };

// Títulos, vista previa al compartir, sitemap y robots. No conoce los datos ni
// los textos del cliente: compara con lo que publica la API.

// Un crawler de vistas previas lee solo el HTML del servidor: así Next pone los
// metadatos en el <head> y el test ve lo mismo que WhatsApp.
const previewBot = { userAgent: "WhatsApp/2.23.20.0 A", javaScriptEnabled: false };

async function publishedCodes(request: APIRequestContext): Promise<string[]> {
  const codes: string[] = [];
  for (let offset = 0; ; offset += 100) {
    const response = await request.get(`/api/products?limit=100&offset=${offset}`);
    expect(response.ok()).toBe(true);
    const page = (await response.json()) as ApiPage;
    codes.push(...page.items.map((item) => item.code));
    if (!page.has_more) return codes;
  }
}

async function productWithCover(request: APIRequestContext): Promise<ApiDetail> {
  for (const code of await publishedCodes(request)) {
    const detail = (await (
      await request.get(`/api/products/${code.toLowerCase()}`)
    ).json()) as ApiDetail;
    if (detail.images.length > 0) return detail;
  }
  throw new Error("No hay productos publicados con fotos: corré `make seed`.");
}

function meta(page: Page, property: string) {
  return page.locator(`head meta[property="${property}"]`).getAttribute("content");
}

async function head(page: Page) {
  return {
    title: await page.title(),
    description: await page.locator('head meta[name="description"]').getAttribute("content"),
  };
}

test.describe("vista previa del detalle", () => {
  test.use(previewBot);

  test("muestra nombre, precio y portada con URLs absolutas sin query", async ({
    page,
    request,
  }) => {
    const store = (await (await request.get("/api/store")).json()) as ApiStore;
    const product = await productWithCover(request);
    const path = `/p/${product.code.toLowerCase()}`;
    const cover = product.images[0];

    // Con utm_source (#34) el canonical y og:url siguen sin query.
    await page.goto(`${path}?utm_source=whatsapp`);

    expect(await page.title()).toContain(product.name);
    expect(await meta(page, "og:title")).toBe(product.name);
    expect(await meta(page, "og:site_name")).toBe(store.name);

    const price = formatPrice(product.price, product.currency, store.locale, store.price_decimals);
    const description = await meta(page, "og:description");
    expect(description?.startsWith(price)).toBe(true);
    expect(await page.locator('head meta[name="description"]').getAttribute("content")).toBe(
      description,
    );

    const image = new URL((await meta(page, "og:image"))!);
    expect(image.pathname).toBe(cover.full);
    expect(await meta(page, "og:image:width")).toBe(String(cover.width));
    expect(await meta(page, "og:image:height")).toBe(String(cover.height));

    const url = new URL((await meta(page, "og:url"))!);
    const canonical = new URL(
      (await page.locator('head link[rel="canonical"]').getAttribute("href"))!,
    );
    for (const absolute of [url, canonical]) {
      expect(absolute.origin).toBe(image.origin);
      expect(absolute.pathname).toBe(path);
      expect(absolute.search).toBe("");
    }

    // La imagen existe y entra en el límite de WhatsApp (600 KB).
    const photo = await request.get(image.pathname);
    expect(photo.ok()).toBe(true);
    expect(photo.headers()["content-type"]).toMatch(/^image\//);
    expect((await photo.body()).length).toBeLessThan(600 * 1024);
  });
});

test.describe("títulos por página", () => {
  test.use(previewBot);

  test("cada página tiene título y descripción propios", async ({ page }) => {
    const pages = [];
    for (const path of ["/", "/stock", "/encargue", "/no-existe-esta-pagina"]) {
      await page.goto(path);
      pages.push(await head(page));
    }
    for (const { title, description } of pages) {
      expect(title).not.toBe("");
      expect(description ?? "").not.toBe("");
    }
    expect(new Set(pages.map((p) => p.title)).size).toBe(pages.length);
    expect(new Set(pages.map((p) => p.description)).size).toBe(pages.length);
  });
});

function escapeRegExp(text: string) {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

// Lo que queda en el <head> después de que corre el JS (#55). El HTML del servidor
// ya trae el título correcto y el navegador puede pisarlo al renderizar: por eso
// se espera al <h1> del 404, que lo dibuja el render del cliente, y se compara
// contra sus textos (los mismos del diccionario que usa la metadata del 404).
async function expectNotFoundHead(page: Page, storeName: string) {
  const main = page.getByRole("main");
  const heading = main.getByRole("heading", { level: 1 });
  await expect(heading).toBeVisible();
  await page.waitForLoadState("networkidle");
  const title = (await heading.textContent())!;
  const text = (await main.locator("h1 + p").textContent())!;

  await expect(page).not.toHaveTitle(storeName);
  await expect(page).toHaveTitle(
    new RegExp(`^${escapeRegExp(title)}.*${escapeRegExp(storeName)}$`),
  );
  const description = page.locator('head meta[name="description"]');
  await expect(description).toHaveCount(1);
  await expect(description).toHaveAttribute("content", text);
  await expect(page.locator('head meta[name="robots"]')).toHaveAttribute("content", /noindex/);
}

test.describe("títulos en el navegador", () => {
  for (const path of ["/p/no-existe-999", "/no-existe/tampoco"]) {
    test(`${path} conserva título y descripción del 404 después de hidratar`, async ({
      page,
      request,
    }) => {
      const store = (await (await request.get("/api/store")).json()) as ApiStore;

      const response = await page.goto(path);

      expect(response?.status()).toBe(404);
      await expectNotFoundHead(page, store.name);
    });
  }

  test("navegar del lado del cliente a una URL inexistente muestra el título del 404", async ({
    page,
    request,
  }) => {
    const store = (await (await request.get("/api/store")).json()) as ApiStore;
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // window.next.router no es API pública, pero es la única forma de navegar
    // sin recargar a una URL que ningún link de la tienda apunta.
    await page.evaluate(() =>
      (window as unknown as { next: { router: { push(href: string): void } } }).next.router.push(
        "/no-existe/tampoco",
      ),
    );

    await expect(page).toHaveURL("/no-existe/tampoco");
    await expectNotFoundHead(page, store.name);
  });

  test("el detalle de un producto conserva su título después de hidratar", async ({
    page,
    request,
  }) => {
    const [code] = await publishedCodes(request);
    const product = (await (
      await request.get(`/api/products/${code.toLowerCase()}`)
    ).json()) as ApiDetail;

    await page.goto(`/p/${code.toLowerCase()}`);

    await expect(page.getByRole("heading", { level: 1 })).toHaveText(product.name);
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveTitle(new RegExp(`^${escapeRegExp(product.name)}`));
  });
});

test.describe("sitemap y robots", () => {
  // No dependen del dispositivo: alcanza con correrlos una vez.
  test.skip(({ isMobile }) => isMobile, "igual en celular y escritorio");

  test("sitemap.xml lista las páginas fijas y todos los productos publicados", async ({
    request,
  }) => {
    const response = await request.get("/sitemap.xml");
    expect(response.ok()).toBe(true);
    expect(response.headers()["content-type"]).toContain("xml");

    const locs = [...(await response.text()).matchAll(/<loc>([^<]+)<\/loc>/g)].map(
      ([, loc]) => new URL(loc),
    );
    expect(new Set(locs.map((loc) => loc.origin)).size).toBe(1);

    const paths = locs.map((loc) => loc.pathname);
    const products = paths.filter((path) => path.startsWith("/p/")).sort();
    const expected = (await publishedCodes(request)).map((c) => `/p/${c.toLowerCase()}`).sort();
    // Igualdad de conjuntos: todos los publicados y ningún oculto o archivado.
    expect(products).toEqual(expected);

    for (const path of ["/", "/stock", "/encargue", "/como-comprar"]) {
      expect(paths).toContain(path);
    }
  });

  for (const path of ["/", "/stock", "/encargue", "/como-comprar"]) {
    test(`la página fija ${path} del sitemap existe`, async ({ request }) => {
      expect((await request.get(path)).status()).toBe(200);
    });
  }

  test("robots.txt excluye el admin y la API y apunta al sitemap", async ({ request }) => {
    const response = await request.get("/robots.txt");
    expect(response.ok()).toBe(true);
    const lines = (await response.text()).split("\n").map((line) => line.trim());
    expect(lines).toContain("Disallow: /admin");
    expect(lines).toContain("Disallow: /api");
    expect(lines.some((line) => /^Sitemap: https?:\/\/.+\/sitemap\.xml$/.test(line))).toBe(true);
  });
});
