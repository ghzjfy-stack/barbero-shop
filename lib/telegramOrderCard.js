/**
 * Minox-style Telegram order card (HTML + inline keyboard).
 */

const MAX_TEXT = 3900;

export function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

export function formatIls(amount) {
  const n = Number(amount);
  if (!Number.isFinite(n)) return "—";
  return `₪${n.toLocaleString("he-IL")}`;
}

export function formatWhen(iso) {
  try {
    return new Intl.DateTimeFormat("he-IL", {
      timeZone: "Asia/Jerusalem",
      day: "2-digit",
      month: "2-digit",
      year: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date(iso || Date.now()));
  } catch {
    return new Date(iso || Date.now()).toISOString();
  }
}

/** Normalize Israeli mobile to wa.me digits (972…). */
export function whatsappDigits(phone) {
  let digits = String(phone || "").replace(/[^\d]/g, "");
  if (!digits) return "";
  if (digits.startsWith("972")) return digits;
  if (digits.startsWith("0")) return `972${digits.slice(1)}`;
  if (digits.length === 9) return `972${digits}`;
  return digits;
}

export function paymentLabelOf(payment) {
  return payment === "paypal" || payment === "PayPal" ? "PayPal" : "ביט";
}

export function waitingStatusOf(payment) {
  return paymentLabelOf(payment) === "PayPal" ? "ממתין ל-PayPal" : "ממתין לביט";
}

function itemsLine(lines = []) {
  if (!Array.isArray(lines) || lines.length === 0) {
    if (typeof lines === "string" && lines.trim()) return lines.trim();
    return "—";
  }
  return lines
    .map((line) => {
      const qty = Number(line.qty) || 1;
      const label = line.label ? ` (${line.label})` : "";
      return `${line.name || "מוצר"}${label} ×${qty}`;
    })
    .join(" · ");
}

function addressLine(details = {}) {
  const parts = [details.address, details.city, details.postal].filter((p) => String(p || "").trim());
  return parts.length ? parts.join(", ") : "—";
}

/**
 * @param {object} order — site checkout shape or Sheets get shape
 * @param {{ status?: string }} [opts]
 */
export function buildOrderCard(order, opts = {}) {
  const details = order.details || {};
  const payment = order.payment === "paypal" || order.payment === "PayPal" ? "paypal" : "bit";
  const status =
    opts.status ||
    order.status ||
    waitingStatusOf(payment);
  const number = order.number || order.orderNumber || "—";
  const phone = String(details.phone || order.phone || "").trim();
  const email = String(details.email || order.email || "").trim();
  const name = String(details.name || order.name || "—").trim() || "—";
  const unit = String(details.unit || order.unit || "").trim() || "—";
  const notes = String(details.notes || order.notes || "").trim() || "—";
  const items = order.itemsText || itemsLine(order.lines || order.items);
  const total = order.total;
  const when = formatWhen(order.createdAt || order.created);

  const text = [
    `🧾 <b>הזמנה #${escapeHtml(number)}</b>`,
    "",
    `📌 <b>סטטוס:</b> ${escapeHtml(status)}`,
    `👤 <b>לקוח:</b> ${escapeHtml(name)}`,
    `✉️ <b>אימייל:</b> ${email ? escapeHtml(email) : "—"}`,
    `📞 <b>טלפון:</b> ${phone ? escapeHtml(phone) : "—"}`,
    `🛒 <b>מוצר:</b> ${escapeHtml(items)}`,
    `💰 <b>סכום:</b> ${escapeHtml(formatIls(total))}`,
    `🏠 <b>כתובת:</b> ${escapeHtml(addressLine({ ...details, address: details.address || order.address, city: details.city || order.city, postal: details.postal || order.postal }))}`,
    `🏢 <b>קומה/דירה:</b> ${escapeHtml(unit)}`,
    `📝 <b>הערות:</b> ${escapeHtml(notes)}`,
    `🕒 <b>נוצרה:</b> ${escapeHtml(when)}`,
  ]
    .join("\n")
    .slice(0, MAX_TEXT);

  return { text, number, phone, status, payment };
}

/**
 * Inline keyboard like Minox: approve / cancel / WhatsApp / refresh.
 * callback_data max 64 bytes — keep short: brb:{a|c|r}:{orderNumber}
 */
export function buildOrderKeyboard(order, opts = {}) {
  const number = String(order.number || order.orderNumber || "").trim();
  const short = number.slice(0, 24);
  const phone = String(order.details?.phone || order.phone || "").trim();
  const wa = whatsappDigits(phone);
  const status = opts.status || order.status || "";
  const done = status === "שולם" || status === "בוטל" || status === "נמסר";

  const rows = [];

  if (!done && short) {
    rows.push([
      { text: `❌ בטל #${short}`, callback_data: `brb:c:${short}` },
      { text: `✅ אשר #${short}`, callback_data: `brb:a:${short}` },
    ]);
  }

  if (wa) {
    const name = String(order.details?.name || order.name || "").trim();
    const hello = name ? `שלום ${name}, לגבי הזמנה ${number} מ-BARBERO: ` : `שלום, לגבי הזמנה ${number} מ-BARBERO: `;
    rows.push([
      {
        text: "📱 שלח ללקוח וואטסאפ",
        url: `https://wa.me/${wa}?text=${encodeURIComponent(hello)}`,
      },
    ]);
  }

  if (short) {
    rows.push([{ text: "🔄 רענן כרטיס", callback_data: `brb:r:${short}` }]);
  }

  return rows.length ? { inline_keyboard: rows } : undefined;
}

export function parseCallbackData(data) {
  const raw = String(data || "");
  const match = /^brb:([acr]):(.+)$/.exec(raw);
  if (!match) return null;
  const action = { a: "approve", c: "cancel", r: "refresh" }[match[1]];
  if (!action) return null;
  return { action, orderNumber: match[2].trim() };
}
