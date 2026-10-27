import { findProduct, formatPrice, resolveOffer } from "./data";
import { currentPath, replaceUrl } from "./navigate";

/** Clean product URL for ads / WhatsApp: https://site/p/wahl-vapor-switch */
export function productPath(productId) {
  return `/p/${encodeURIComponent(productId)}`;
}

export function productPageUrl(productId) {
  return new URL(productPath(productId), window.location.origin).toString();
}

/** Resolve product id from `/p/:id` or legacy `?product=` (no visual change to the shop). */
export function parseProductFromLocation() {
  try {
    const path = currentPath();
    const match = path.match(/^\/p\/([^/]+)$/);
    if (match) {
      const id = decodeURIComponent(match[1]);
      return findProduct(id) ? id : null;
    }
    const q = new URLSearchParams(window.location.search).get("product");
    return q && findProduct(q) ? q : null;
  } catch {
    return null;
  }
}

export function syncProductLocation(productId) {
  const url = new URL(window.location.href);
  url.searchParams.delete("product");

  if (productId) {
    url.pathname = productPath(productId);
    url.hash = "";
  } else if (/^\/p\//.test(url.pathname.replace(/\/$/, "") || "/")) {
    url.pathname = "/";
    url.hash = "collection";
  }

  const next = `${url.pathname}${url.search}${url.hash}`;
  const current = `${window.location.pathname}${window.location.search}${window.location.hash}`;
  if (current !== next) {
    replaceUrl(next);
  }
}

/** @deprecated use syncProductLocation */
export function syncProductQuery(productId) {
  syncProductLocation(productId);
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
