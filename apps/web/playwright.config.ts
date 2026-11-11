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
    { name: "escritorio", use: { ...devices["Desktop Chrome"] } },
    { name: "celular", use: { ...devices["Pixel 7"] } },
  ],
});
