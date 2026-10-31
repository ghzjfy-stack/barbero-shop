/**
 * Meta Conversions API (server) — Purchase when an order is marked paid.
 * Env (Vercel Production + Preview):
 *   META_PIXEL_ID            — same digits as VITE_META_PIXEL_ID (fallback hardcoded)
 *   META_CAPI_ACCESS_TOKEN   — Events Manager → Settings → Generate access token
 *
 * event_id = order number so browser «אישרתי ששילמתי» + CAPI dedupe.
 */

const DEFAULT_PIXEL = "1131099525966263";

function pixelId() {
  return String(process.env.META_PIXEL_ID || process.env.VITE_META_PIXEL_ID || DEFAULT_PIXEL).trim();
}

function accessToken() {
  return String(process.env.META_CAPI_ACCESS_TOKEN || "").trim();
}

function contentsFromOrder(order = {}) {
  const lines = Array.isArray(order.lines) ? order.lines : [];
  if (lines.length) {
    return lines.map((line) => ({
      id: String(line.id || line.name || "item"),
      quantity: Math.max(1, Number(line.qty) || 1),
      item_price: Number(line.unitPrice ?? line.price) || undefined,
    }));
  }
  return undefined;
}

/**
 * @param {object} order — { number, total, lines?, details? }
 * @param {{ eventSourceUrl?: string }} [opts]
 */
export async function sendMetaPurchaseCapi(order, opts = {}) {
  const token = accessToken();
  const id = pixelId();
  if (!token || !id || !order?.number) {
    return { ok: false, skipped: true, reason: !token ? "no_token" : "missing_order" };
  }

  const eventTime = Math.floor(Date.now() / 1000);
  async function sha256(value) {
    const data = new TextEncoder().encode(String(value).trim().toLowerCase());
    const buf = await crypto.subtle.digest("SHA-256", data);
    return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
  }

  const userData = {
    // Always send external_id so Meta accepts the event even without email/phone.
    external_id: [await sha256(String(order.number))],
  };
  const email = String(order.details?.email || order.email || "").trim().toLowerCase();
  const phone = String(order.details?.phone || order.phone || "").replace(/\D/g, "");
  if (email) userData.em = [await sha256(email)];
  if (phone) {
    const normalized = phone.startsWith("972") ? phone : phone.replace(/^0/, "972");
    userData.ph = [await sha256(normalized)];
  }

  const contents = contentsFromOrder(order);
  const customData = {
    currency: "ILS",
    value: Number(order.total) || 0,
    content_type: "product",
    order_id: String(order.number),
  };
  if (contents) {
    customData.contents = contents;
    customData.content_ids = contents.map((c) => c.id);
    customData.num_items = contents.reduce((sum, c) => sum + c.quantity, 0);
  }

  const body = {
    data: [
      {
        event_name: "Purchase",
        event_time: eventTime,
        event_id: String(order.number),
        action_source: "website",
        event_source_url: opts.eventSourceUrl || "https://www.barbero.co.il/",
        user_data: userData,
        custom_data: customData,
      },
    ],
  };

  const url = `https://graph.facebook.com/v21.0/${encodeURIComponent(id)}/events?access_token=${encodeURIComponent(token)}`;
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || data.error) {
      return { ok: false, error: data.error?.message || `http_${res.status}`, data };
    }
    return { ok: true, data };
  } catch (error) {
    return { ok: false, error: error?.message || "capi_failed" };
  }
}
