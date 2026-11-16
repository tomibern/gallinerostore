// URL pública del sitio (SITE_URL): la misma variable que usa la API para el
// link del mensaje prearmado. Con ella se arman las URLs absolutas de Open
// Graph, el canonical, el sitemap y el robots.txt.

const DEFAULT_SITE_URL = "http://localhost:3000";

/** Valida SITE_URL. Un valor inválido corta el arranque, no un render a mitad de camino. */
export function parseSiteUrl(raw: string | undefined): URL {
  const value = raw || DEFAULT_SITE_URL;
  const url = URL.canParse(value) ? new URL(value) : null;
  if (!url || (url.protocol !== "http:" && url.protocol !== "https:")) {
    throw new Error(`SITE_URL tiene que ser una URL http o https; llegó «${value}».`);
  }
  return url;
}
