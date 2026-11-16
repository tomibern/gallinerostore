import { expect, type Page } from "@playwright/test";

// Ayudas para el listado paginado: el tamaño de página lo decide el servidor de
// Next (LISTING_PAGE_SIZE), así que los tests lo leen de la grilla.

export const cards = (page: Page) => page.locator("[data-testid=products] > li");

export const loadMoreButton = (page: Page) => page.getByRole("button", { name: "Ver más" });

export async function cardCodes(page: Page): Promise<(string | undefined)[]> {
  return cards(page).evaluateAll((items) => items.map((li) => (li as HTMLElement).dataset.code));
}

export async function pageSizeOf(page: Page): Promise<number> {
  return Number(await page.getByTestId("products").getAttribute("data-page-size"));
}

/**
 * Suma páginas con «Ver más» hasta que no hay más (no depende del scroll). La
 * carga automática puede ganarle al clic: entonces el botón ya no está y listo.
 */
export async function loadAll(page: Page) {
  const button = loadMoreButton(page);
  await expect(async () => {
    if (await button.isVisible()) await button.click({ timeout: 1000 }).catch(() => {});
    await expect(button).toBeHidden({ timeout: 1000 });
  }).toPass();
}

/** Saca IntersectionObserver, como en un navegador donde la carga automática no anda. */
export async function withoutAutoLoad(page: Page) {
  await page.addInitScript(() => {
    // @ts-expect-error: se borra a propósito.
    delete window.IntersectionObserver;
  });
}
