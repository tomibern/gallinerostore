import type { MetadataRoute } from "next";

import { SECTION_PATHS } from "@/components/store/section-page";
import { getPublishedCodes } from "@/lib/api";
import { siteUrl } from "@/lib/env";
import { sitemapEntries } from "@/lib/seo";

// Se arma en cada pedido: en el build no hay API, y SITE_URL es la del entorno
// donde corre, no la del build.
export const dynamic = "force-dynamic";

// «Cómo comprar» es la página de #32.
const STATIC_PATHS = ["/", SECTION_PATHS.stock, SECTION_PATHS.on_order, "/como-comprar"];

// sitemap.xml: home, secciones, «Cómo comprar» y cada producto publicado (la API
// no lista ocultos ni archivados). Si la API falla, error en vez de un sitemap incompleto.
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  return sitemapEntries(siteUrl(), STATIC_PATHS, await getPublishedCodes());
}
