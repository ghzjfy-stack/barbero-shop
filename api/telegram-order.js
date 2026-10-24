/**
 * Vercel serverless: notify Telegram on new Barbero orders.
 *
 * Set in Vercel → Project → Settings → Environment Variables:
 *   TELEGRAM_BOT_TOKEN  — from @BotFather
 *   TELEGRAM_CHAT_ID    — your chat / group / channel id
 */

const MAX_TEXT = 3500;

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function formatIls(amount) {
  const n = Number(amount);
  if (!Number.isFinite(n)) return "—";
  return `₪${n.toLocaleString("he-IL")}`;
}

function formatWhen(iso) {
  try {
    return new Intl.DateTimeFormat("he-IL", {
      timeZone: "Asia/Jerusalem",
      dateStyle: "short",
      timeStyle: "short",
    }).format(new Date(iso || Date.now()));
  } catch {
    return new Date(iso || Date.now()).toISOString();
  }
}

function buildAddress(details = {}) {
  return [details.address, details.unit, details.city, details.postal]
    .map((part) => String(part || "").trim())
    .filter(Boolean)
    .join(", ");
}

function buildItems(lines = []) {
  if (!Array.isArray(lines) || lines.length === 0) return "—";
  return lines
    .map((line) => {
      const title = [line.name, line.model, line.label].filter(Boolean).join(" · ");
      const qty = Number(line.qty) || 1;
      const total = formatIls(line.lineTotal);
      return `• ${escapeHtml(title)} × ${qty} — ${escapeHtml(total)}`;
    })
    .join("\n");
}

function buildMessage(order) {
  const details = order.details || {};
  const when = formatWhen(order.createdAt);
  const address = buildAddress(details);
  const notes = String(details.notes || "").trim() || "—";
  const items = buildItems(order.lines);

  return [
    "🛒 <b>הזמנה חדשה — BARBERO</b>",
    "",
    `<b>מספר:</b> ${escapeHtml(order.number || "—")}`,
    `<b>תאריך/שעה:</b> ${escapeHtml(when)}`,
    "",
    `<b>שם:</b> ${escapeHtml(details.name || "—")}`,
    `<b>טלפון:</b> ${escapeHtml(details.phone || "—")}`,
    `<b>כתובת:</b> ${escapeHtml(address || "—")}`,
    `<b>הערות:</b> ${escapeHtml(notes)}`,
    "",
    "<b>פריטים / שירות:</b>",
    items,
    "",
    `<b>ביניים:</b> ${escapeHtml(formatIls(order.subtotal))}`,
    `<b>משלוח:</b> ${escapeHtml(formatIls(order.shipping))}`,
    `<b>סה״כ לתשלום:</b> ${escapeHtml(formatIls(order.total))}`,
  ].join("\n");
}

function readJson(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on("data", (chunk) => chunks.push(chunk));
    req.on("end", () => {
      try {
        const raw = Buffer.concat(chunks).toString("utf8");
        resolve(raw ? JSON.parse(raw) : {});
      } catch (error) {
        reject(error);
      }
    });
    req.on("error", reject);
  });
}

function sendJson(res, status, body) {
  res.statusCode = status;
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  res.end(JSON.stringify(body));
}

export default async function handler(req, res) {
  res.setHeader("Cache-Control", "no-store");

  if (req.method === "OPTIONS") {
    res.statusCode = 204;
    res.end();
    return;
  }

  if (req.method !== "POST") {
    sendJson(res, 405, { ok: false, error: "method_not_allowed" });
    return;
  }

  const token = process.env.TELEGRAM_BOT_TOKEN;
  const chatId = process.env.TELEGRAM_CHAT_ID;

  if (!token || !chatId) {
    sendJson(res, 503, {
      ok: false,
      error: "telegram_not_configured",
      hint: "Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in Vercel env",
    });
    return;
  }

  let order;
  try {
    order = await readJson(req);
  } catch {
    sendJson(res, 400, { ok: false, error: "invalid_json" });
    return;
  }

  if (!order || typeof order !== "object" || !order.number || !order.details) {
    sendJson(res, 400, { ok: false, error: "invalid_order" });
    return;
  }

  const text = buildMessage(order).slice(0, MAX_TEXT);
  const telegramUrl = `https://api.telegram.org/bot${token}/sendMessage`;

  let telegramRes;
  try {
    telegramRes = await fetch(telegramUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        chat_id: chatId,
        text,
        parse_mode: "HTML",
        disable_web_page_preview: true,
      }),
    });
  } catch {
    sendJson(res, 502, { ok: false, error: "telegram_unreachable" });
    return;
  }

  const payload = await telegramRes.json().catch(() => ({}));
  if (!telegramRes.ok || !payload.ok) {
    sendJson(res, 502, {
      ok: false,
      error: "telegram_rejected",
      detail: payload.description || telegramRes.statusText,
    });
    return;
  }

  sendJson(res, 200, { ok: true });
}
