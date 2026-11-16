import type { MetadataRoute } from "next";

import { siteUrl } from "@/lib/env";

// Lee SITE_URL en cada pedido, no la del build.
export const dynamic = "force-dynamic";

// robots.txt: fuera el admin y la API. No protege nada (eso lo hace el login):
// solo pide a los buscadores que no los recorran. /media queda permitido porque
// ahí están las fotos que leen las vistas previas.
export default function robots(): MetadataRoute.Robots {
  return {
    rules: { userAgent: "*", allow: "/", disallow: ["/admin", "/api"] },
    sitemap: new URL("/sitemap.xml", siteUrl()).href,
  };
}
