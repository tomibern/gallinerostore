import { expect, test, type APIRequestContext } from "@playwright/test";

// Recuperación de la contraseña de punta a punta: pide el link, lo lee del email en
// Mailpit, elige la contraseña y entra al panel. Corre en su propio proyecto, antes que
// los demás (playwright.config.ts): al usar el link se cortan todas las sesiones del
// admin. Vuelve a poner la misma contraseña del admin de prueba, así los demás tests
// siguen entrando con ella.
const EMAIL = process.env.SEED_ADMIN_EMAIL ?? "admin@example.com";
const PASSWORD = process.env.SEED_ADMIN_PASSWORD ?? "admin-de-prueba";
const MAILPIT_URL = process.env.MAILPIT_URL ?? "http://localhost:8025";

type MailpitSummary = { ID: string; Created: string };

/** El link para elegir contraseña del último email al admin llegado después de `since`. */
async function passwordLink(request: APIRequestContext, since: Date): Promise<string> {
  let link = "";
  await expect
    .poll(
      async () => {
        const search = await request.get(`${MAILPIT_URL}/api/v1/search`, {
          params: { query: `to:"${EMAIL}"` },
        });
        const { messages } = (await search.json()) as { messages: MailpitSummary[] };
        const latest = messages.find((message) => new Date(message.Created) >= since);
        if (!latest) return "";
        const message = await request.get(`${MAILPIT_URL}/api/v1/message/${latest.ID}`);
        const { Text } = (await message.json()) as { Text: string };
        link = Text.match(/https?:\/\/\S+\/admin\/elegir-contrasena#token=\S+/)?.[0] ?? "";
        return link;
      },
      { message: "el email con el link llega a Mailpit" },
    )
    .not.toBe("");
  return link;
}

test("el admin recupera la contraseña con el link del email y entra al panel", async ({
  page,
  request,
}) => {
  // Mailpit guarda la hora con segundos: un margen chico evita perder el email.
  const since = new Date(Date.now() - 2000);
  await page.goto("/admin/login");
  await page.getByRole("link", { name: "Olvidé mi contraseña" }).click();

  await expect(page).toHaveURL(/\/admin\/recuperar$/);
  await page.getByLabel("Email").fill(EMAIL);
  await page.getByRole("button", { name: "Mandar el link" }).click();
  await expect(page.getByRole("status")).toHaveText(/Si el email es el del admin/);

  const link = new URL(await passwordLink(request, since));
  await page.goto(`${link.pathname}${link.hash}`);

  await expect(page.getByRole("heading", { name: "Elegir contraseña" })).toBeVisible();
  await page.getByLabel("Contraseña nueva", { exact: true }).fill(PASSWORD);
  await page.getByLabel("Repetí la contraseña nueva").fill(PASSWORD);
  await page.getByRole("button", { name: "Guardar y entrar" }).click();

  await expect(page).toHaveURL(/\/admin\/productos$/);

  // El link sirve una sola vez.
  await page.goto(`${link.pathname}${link.hash}`);
  await page.getByLabel("Contraseña nueva", { exact: true }).fill(PASSWORD);
  await page.getByLabel("Repetí la contraseña nueva").fill(PASSWORD);
  await page.getByRole("button", { name: "Guardar y entrar" }).click();
  await expect(page.getByRole("main").getByRole("alert")).toHaveText(
    "El link venció o ya se usó. Pedí uno nuevo.",
  );
});
