/**
 * Meta (Facebook) Pixel — public Pixel ID via VITE_META_PIXEL_ID.
 * Events Manager → Data sources → Pixel → copy Pixel ID (numbers only).
 */

const PIXEL_ID = String(import.meta.env.VITE_META_PIXEL_ID || "").trim();

export function isMetaPixelEnabled() {
  return Boolean(PIXEL_ID);
}

export function ensureMetaPixel() {
  if (typeof window === "undefined" || !PIXEL_ID) return false;
  if (window.fbq && window.__barberoMetaPixelId === PIXEL_ID) return true;

  if (!window.fbq) {
    !(function (f, b, e, v, n, t, s) {
      if (f.fbq) return;
      n = f.fbq = function () {
        n.callMethod ? n.callMethod.apply(n, arguments) : n.queue.push(arguments);
      };
      if (!f._fbq) f._fbq = n;
      n.push = n;
      n.loaded = true;
      n.version = "2.0";
      n.queue = [];
      t = b.createElement(e);
      t.async = true;
      t.src = v;
      s = b.getElementsByTagName(e)[0];
      s.parentNode.insertBefore(t, s);
    })(window, document, "script", "https://connect.facebook.net/en_US/fbevents.js");
  }

  window.__barberoMetaPixelId = PIXEL_ID;
  window.fbq("init", PIXEL_ID);
  return true;
}

function fbqTrack(eventName, params, options) {
  if (!ensureMetaPixel() || typeof window.fbq !== "function") return;
  if (options) window.fbq("track", eventName, params || {}, options);
  else window.fbq("track", eventName, params || {});
}

export function trackMetaPageView() {
  fbqTrack("PageView");
}

function contentFromProduct(product, offer) {
  if (!product) return null;
  const price = Number(offer?.price ?? product.price) || 0;
  return {
    content_ids: [String(product.id)],
    content_name: product.name || product.model || product.id,
    content_type: "product",
    content_category: product.category || undefined,
    value: price,
    currency: "ILS",
  };
}

export function trackMetaViewContent(product, offer) {
  const payload = contentFromProduct(product, offer);
  if (!payload) return;
  fbqTrack("ViewContent", payload);
}

export function trackMetaAddToCart(product, offer, qty = 1) {
  const payload = contentFromProduct(product, offer);
  if (!payload) return;
  const q = Math.max(1, Number(qty) || 1);
  fbqTrack("AddToCart", {
    ...payload,
    value: payload.value * q,
    contents: [{ id: String(product.id), quantity: q }],
    num_items: q,
  });
}

export function trackMetaInitiateCheckout({ value, numItems, contentIds } = {}) {
  fbqTrack("InitiateCheckout", {
    value: Number(value) || 0,
    currency: "ILS",
    num_items: Number(numItems) || 1,
    content_ids: Array.isArray(contentIds) ? contentIds.map(String) : undefined,
    content_type: "product",
  });
}

export function trackMetaPurchase(order) {
  if (!order) return;
  const contents = (order.lines || []).map((line) => ({
    id: String(line.id || line.name),
    quantity: Number(line.qty) || 1,
    item_price: Number(line.unitPrice) || undefined,
  }));
  fbqTrack(
    "Purchase",
    {
      value: Number(order.total) || 0,
      currency: "ILS",
      contents,
      content_ids: contents.map((c) => c.id),
      content_type: "product",
      num_items: contents.reduce((sum, c) => sum + c.quantity, 0),
    },
    order.number ? { eventID: String(order.number) } : undefined,
  );
}
