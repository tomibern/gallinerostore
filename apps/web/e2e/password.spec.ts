import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

// Cambiar y recuperar la contraseña de punta a punta. Corre en su propio proyecto, antes
// que los demás (playwright.config.ts): cambiarla o usar el link de recuperación corta
// las sesiones del admin. Los tests van en orden, uno por vez, y aunque falle uno siguen
// los demás: la recuperación, al final, deja siempre la contraseña del admin de prueba,
// así los demás tests siguen entrando con ella.
test.describe.configure({ mode: "default" });

const EMAIL = process.env.SEED_ADMIN_EMAIL ?? "admin@example.com";
const PASSWORD = process.env.SEED_ADMIN_PASSWORD ?? "admin-de-prueba";
const TEMPORARY = `${PASSWORD}-cambiada`;
const MAILPIT_URL = process.env.MAILPIT_URL ?? "http://localhost:8025";

async function logIn(page: Page, password: string) {
  await page.goto("/admin/login");
  await page.getByLabel("Email").fill(EMAIL);
  await page.getByLabel("Contraseña").fill(password);
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page).toHaveURL(/\/admin\/productos$/);
}

/** El formulario de «Cambiar contraseña» de Cuenta (la página tiene otro «Guardar»). */
const passwordForm = (page: Page) => page.getByRole("form", { name: "Cambiar la contraseña" });

/** Abre «Cambiar contraseña» en Cuenta y la cambia de `from` a `to`. */
async function changePassword(page: Page, from: string, to: string) {
  await page.getByRole("button", { name: "Cambiar contraseña" }).click();
  const form = passwordForm(page);
  await form.getByLabel("Contraseña actual").fill(from);
  await form.getByLabel("Contraseña nueva", { exact: true }).fill(to);
  await form.getByLabel("Repetí la contraseña nueva").fill(to);
  await form.getByRole("button", { name: "Guardar" }).click();
  await expect(page.getByText("Listo: cambiaste la contraseña")).toBeVisible();
  await expect(form).toHaveCount(0);
}

test("cambiar la contraseña es una opción de Cuenta y después se entra con la nueva", async ({
  page,
}) => {
  await logIn(page, PASSWORD);
  await page.goto("/admin/contenido");

  // Cerrado: solo el botón, sin los campos.
  await expect(page.getByRole("button", { name: "Cambiar contraseña" })).toBeVisible();
  await expect(passwordForm(page)).toHaveCount(0);
  await expect(page.getByRole("main").getByRole("button", { name: "Cerrar sesión" })).toBeVisible();

  // Cancelar cierra y borra lo escrito.
  const form = passwordForm(page);
  await page.getByRole("button", { name: "Cambiar contraseña" }).click();
  await form.getByLabel("Contraseña actual").fill("algo-escrito");
  await form.getByRole("button", { name: "Cancelar" }).click();
  await expect(form).toHaveCount(0);
  await page.getByRole("button", { name: "Cambiar contraseña" }).click();
  await expect(form.getByLabel("Contraseña actual")).toHaveValue("");

  // Con la actual incorrecta sigue abierto con el error.
  await form.getByLabel("Contraseña actual").fill("no-es-esta-clave");
  await form.getByLabel("Contraseña nueva", { exact: true }).fill(TEMPORARY);
  await form.getByLabel("Repetí la contraseña nueva").fill(TEMPORARY);
  await form.getByRole("button", { name: "Guardar" }).click();
  await expect(form.getByRole("alert")).toHaveText("La contraseña actual no es correcta.");
  await form.getByRole("button", { name: "Cancelar" }).click();

  await changePassword(page, PASSWORD, TEMPORARY);

  // Entra con la nueva y la vuelve a dejar como estaba.
  await page.getByRole("main").getByRole("button", { name: "Cerrar sesión" }).click();
  await logIn(page, TEMPORARY);
  await page.goto("/admin/contenido");
  await changePassword(page, TEMPORARY, PASSWORD);
});

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
