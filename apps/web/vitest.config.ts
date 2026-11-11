import { defineConfig } from "vitest/config";

// Tests unitarios de la web. Los de punta a punta van con Playwright (#8).
export default defineConfig({
  test: {
    include: ["**/*.test.{ts,tsx}"],
    exclude: ["node_modules/**", ".next/**", "e2e/**"],
    passWithNoTests: true,
  },
});
