/**
 * Arma el link de WhatsApp con un mensaje prearmado para consultar una prenda.
 * Se usa wa.me porque funciona igual en mobile (abre la app) y desktop (WhatsApp Web).
 */
export function buildWhatsAppLink(
  phone: string,
  product?: { name: string; size?: string },
): string {
  const digits = phone.replace(/\D/g, "");
  if (!digits) throw new Error("Número de WhatsApp inválido");

  const message = product
    ? `Hola! Me interesa la camiseta ${product.name}${product.size ? ` talle ${product.size}` : ""}. ¿Está disponible?`
    : "Hola! Quería hacer una consulta sobre las camisetas.";

  return `https://wa.me/${digits}?text=${encodeURIComponent(message)}`;
}

export function buildInstagramLink(user: string): string {
  return `https://instagram.com/${user.replace(/^@/, "")}`;
}
