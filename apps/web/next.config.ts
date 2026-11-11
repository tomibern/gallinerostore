import { networkInterfaces } from "node:os";
import { join } from "node:path";

import type { NextConfig } from "next";

// En desarrollo las variables viven en el .env de la raíz del monorepo.
try {
  process.loadEnvFile(join(import.meta.dirname, "../../.env"));
} catch {
  // Sin .env: en producción las variables las pone el hosting.
}

const apiInternalUrl = process.env.API_INTERNAL_URL ?? "http://localhost:8000";

// Next bloquea por defecto los pedidos de desarrollo desde otras direcciones.
// Habilitamos las IPs de esta máquina para probar desde el celular en la misma red.
const lanAddresses = Object.values(networkInterfaces())
  .flat()
  .filter((net) => net && net.family === "IPv4" && !net.internal)
  .map((net) => net!.address);

const nextConfig: NextConfig = {
  allowedDevOrigins: lanAddresses,
  // El navegador solo habla con Next; la API va detrás (ADR 0003).
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${apiInternalUrl}/:path*` }];
  },
};

export default nextConfig;
