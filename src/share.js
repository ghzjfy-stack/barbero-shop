import { formatPrice, resolveOffer } from "./data";

export function productPageUrl(productId) {
  const url = new URL(window.location.href);
  url.searchParams.set("product", productId);
  url.hash = "collection";
  return url.toString();
}

export function syncProductQuery(productId) {
  const url = new URL(window.location.href);
  if (productId) url.searchParams.set("product", productId);
  else url.searchParams.delete("product");
  const next = `${url.pathname}${url.search}${url.hash}`;
  if (`${window.location.pathname}${window.location.search}${window.location.hash}` !== next) {
    window.history.replaceState({}, "", next);
  }
}

export function productWhatsAppShareHref(product, variantId) {
  const offer = resolveOffer(product, variantId);
  const lines = [
    "ראיתי ב-BARBERO וחשבתי שזה יעניין אותך:",
    `${product.name} — ${formatPrice(offer.price)}`,
    productPageUrl(product.id),
  ];
  return `https://wa.me/?text=${encodeURIComponent(lines.join("\n"))}`;
}
