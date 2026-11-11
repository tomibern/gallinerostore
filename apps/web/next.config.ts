import { networkInterfaces } from "node:os";
import { join } from "node:path";

import type { NextConfig } from "next";

import { apiInternalUrl, mediaInternalUrl } from "./lib/env";

// En desarrollo las variables viven en el .env de la raíz del monorepo.
try {
  process.loadEnvFile(join(import.meta.dirname, "../../.env"));
} catch {
  // Sin .env: en producción las variables las pone el hosting.
}

// Next bloquea por defecto los pedidos de desarrollo desde otras direcciones.
// Habilitamos las IPs de esta máquina para probar desde el celular en la misma red.
const lanAddresses = Object.values(networkInterfaces())
  .flat()
  .filter((net) => net && net.family === "IPv4" && !net.internal)
  .map((net) => net!.address);

const nextConfig: NextConfig = {
  allowedDevOrigins: lanAddresses,
  // El cliente generado se publica como TypeScript dentro del monorepo.
  transpilePackages: ["@catalog/api-client"],
  // El navegador solo habla con Next; la API y las fotos van detrás (ADR 0003).
  async rewrites() {
    return [
      { source: "/api/:path*", destination: `${apiInternalUrl()}/:path*` },
      { source: "/media/:path*", destination: `${mediaInternalUrl()}/:path*` },
    ];
  },
};

export default nextConfig;
