import { defineConfig, devices } from "@playwright/test";

// Tests de punta a punta contra el entorno de `make dev` (no levanta nada solo).
// Otra dirección: E2E_BASE_URL=http://192.168.x.x:3000 make e2e
export default defineConfig({
  testDir: "e2e",
  fullyParallel: true,
  reporter: "list",
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000",
    trace: "retain-on-failure",
  },
  projects: [
    // Recuperar la contraseña corta todas las sesiones del admin: corre sola y antes que
    // los demás, que entran al panel.
    {
      name: "contraseña",
      testMatch: /password-recovery\.spec\.ts/,
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "escritorio",
      testIgnore: /password-recovery\.spec\.ts/,
      dependencies: ["contraseña"],
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "celular",
      testIgnore: /password-recovery\.spec\.ts/,
      dependencies: ["contraseña"],
      use: { ...devices["Pixel 7"] },
    },
  ],
});
