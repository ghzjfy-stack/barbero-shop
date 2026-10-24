/**
 * Vercel serverless: push a full order alert into the Telegram orders group.
 *
 * Vercel → Project → Settings → Environment Variables (Production + Preview):
 *   TELEGRAM_BOT_TOKEN          — from @BotFather
 *   TELEGRAM_CHAT_ID            — group id (usually -100…) of קבוצת ההזמנות
 *   TELEGRAM_MESSAGE_THREAD_ID  — optional; forum topic id inside the group
 *
 * Setup:
 * 1. Create a bot with @BotFather → copy the token
 * 2. Add the bot to the orders group (admin recommended)
 * 3. Send any message in the group, then open:
 *      https://api.telegram.org/bot<TOKEN>/getUpdates
 *    and copy chat.id (negative for groups)
 * 4. Paste TOKEN + CHAT_ID into Vercel env and Redeploy
 */

const MAX_TEXT = 3900;

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
      weekday: "short",
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date(iso || Date.now()));
  } catch {
    return new Date(iso || Date.now()).toISOString();
  }
}

function digitsOnly(phone) {
  return String(phone || "").replace(/[^\d+]/g, "");
}

function buildItems(lines = []) {
  if (!Array.isArray(lines) || lines.length === 0) return "—";
  return lines
    .map((line, index) => {
      const qty = Number(line.qty) || 1;
      const unit = Number.isFinite(Number(line.unitPrice))
        ? Number(line.unitPrice)
        : qty > 0 && Number.isFinite(Number(line.lineTotal))
          ? Number(line.lineTotal) / qty
          : null;
      const rows = [
        `<b>${index + 1}.</b> ${escapeHtml(line.name || "מוצר")}`,
        line.model ? `   דגם: ${escapeHtml(line.model)}` : null,
        line.kind ? `   קטגוריה: ${escapeHtml(line.kind)}` : null,
        line.label ? `   אפשרות: ${escapeHtml(line.label)}` : null,
        line.variantId && line.variantId !== "default"
          ? `   מזהה וריאנט: ${escapeHtml(line.variantId)}`
          : null,
        `   כמות: ${qty}`,
        unit != null ? `   מחיר יחידה: ${escapeHtml(formatIls(unit))}` : null,
        `   סה״כ שורה: ${escapeHtml(formatIls(line.lineTotal))}`,
      ];
      return rows.filter(Boolean).join("\n");
    })
    .join("\n\n");
}

function buildMessage(order) {
  const details = order.details || {};
  const when = formatWhen(order.createdAt);
  const phone = String(details.phone || "").trim();
  const phoneDigits = digitsOnly(phone);
  const phoneLine = phone
    ? phoneDigits
      ? `<a href="tel:${escapeHtml(phoneDigits)}">${escapeHtml(phone)}</a>`
      : escapeHtml(phone)
    : "—";
  const notes = String(details.notes || "").trim() || "אין";
  const itemCount = Array.isArray(order.lines)
    ? order.lines.reduce((sum, line) => sum + (Number(line.qty) || 0), 0)
    : 0;

  return [
    "🔔 <b>הזמנה חדשה — BARBERO</b>",
    "קבוצת הזמנות · התראה מהאתר",
    "",
    `<b>מספר הזמנה:</b> <code>${escapeHtml(order.number || "—")}</code>`,
    `<b>תאריך ושעה:</b> ${escapeHtml(when)}`,
    `<b>אמצעי תשלום:</b> ביט בלבד`,
    `<b>סטטוס:</b> ממתין להעברת ביט מהלקוח`,
    "",
    "<b>פרטי לקוח</b>",
    `<b>שם מלא:</b> ${escapeHtml(details.name || "—")}`,
    `<b>טלפון:</b> ${phoneLine}`,
    "",
    "<b>כתובת למשלוח</b>",
    `<b>רחוב / כתובת:</b> ${escapeHtml(details.address || "—")}`,
    `<b>דירה / קומה / כניסה:</b> ${escapeHtml(details.unit || "—")}`,
    `<b>עיר:</b> ${escapeHtml(details.city || "—")}`,
    `<b>מיקוד:</b> ${escapeHtml(details.postal || "—")}`,
    "",
    `<b>הערות מהלקוח:</b> ${escapeHtml(notes)}`,
    "",
    `<b>פריטים בהזמנה</b> (${itemCount})`,
    buildItems(order.lines),
    "",
    "<b>סיכום תשלום</b>",
    `<b>סכום ביניים:</b> ${escapeHtml(formatIls(order.subtotal))}`,
    `<b>משלוח:</b> ${escapeHtml(formatIls(order.shipping))}`,
    `<b>סה״כ לתשלום בביט:</b> ${escapeHtml(formatIls(order.total))}`,
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

function telegramConfig() {
  const token = process.env.TELEGRAM_BOT_TOKEN;
  const chatId = process.env.TELEGRAM_CHAT_ID;
  const threadRaw = process.env.TELEGRAM_MESSAGE_THREAD_ID;
  const threadId = threadRaw && /^\d+$/.test(threadRaw) ? Number(threadRaw) : undefined;
  return { token, chatId, threadId };
}

async function sendTelegramMessage(text) {
  const { token, chatId, threadId } = telegramConfig();
  if (!token || !chatId) {
    return {
      ok: false,
      status: 503,
      body: {
        ok: false,
        error: "telegram_not_configured",
        hint: "Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID (group id) in Vercel env",
      },
    };
  }

  const payload = {
    chat_id: chatId,
    text,
    parse_mode: "HTML",
    disable_web_page_preview: true,
    // false = phone push notification in the Telegram app
    disable_notification: false,
  };
  if (threadId) payload.message_thread_id = threadId;

  let telegramRes;
  try {
    telegramRes = await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch {
    return { ok: false, status: 502, body: { ok: false, error: "telegram_unreachable" } };
  }

  const data = await telegramRes.json().catch(() => ({}));
  if (!telegramRes.ok || !data.ok) {
    return {
      ok: false,
      status: 502,
      body: {
        ok: false,
        error: "telegram_rejected",
        detail: data.description || telegramRes.statusText,
      },
    };
  }

  return { ok: true, status: 200, body: { ok: true, message_id: data.result?.message_id } };
}

export default async function handler(req, res) {
  res.setHeader("Cache-Control", "no-store");

  if (req.method === "OPTIONS") {
    res.statusCode = 204;
    res.end();
    return;
  }

  // GET ?test=1 — send a sample alert to the orders group (for setup checks)
  if (req.method === "GET") {
    const url = new URL(req.url || "/", "http://localhost");
    if (url.searchParams.get("test") !== "1") {
      sendJson(res, 405, { ok: false, error: "method_not_allowed" });
      return;
    }
    const sample = buildMessage({
      number: "BRB-TEST",
      createdAt: new Date().toISOString(),
      details: {
        name: "בדיקת מערכת",
        phone: "054-0000000",
        address: "רחוב לדוגמה 1",
        unit: "דירה 2",
        city: "תל אביב",
        postal: "6100000",
        notes: "זו הודעת בדיקה מקבוצת ההזמנות",
      },
      lines: [
        {
          name: "מוצר בדיקה",
          model: "Demo",
          kind: "מכונות תספורת",
          label: "רגיל",
          qty: 1,
          unitPrice: 100,
          lineTotal: 100,
        },
      ],
      subtotal: 100,
      shipping: 39,
      total: 139,
    });
    const result = await sendTelegramMessage(sample);
    sendJson(res, result.status, result.body);
    return;
  }

  if (req.method !== "POST") {
    sendJson(res, 405, { ok: false, error: "method_not_allowed" });
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
  const result = await sendTelegramMessage(text);
  sendJson(res, result.status, result.body);
}
