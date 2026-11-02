/**
 * Vercel serverless: Minox-style order card → Telegram orders group.
 *
 * Env (Production + Preview):
 *   TELEGRAM_BOT_TOKEN
 *   TELEGRAM_CHAT_ID
 *   TELEGRAM_MESSAGE_THREAD_ID  (optional forum topic)
 *
 * Buttons (approve/cancel/refresh) need webhook:
 *   POST /api/telegram-webhook  + setWebhook (see .env.example)
 *
 * On each new order also sends a short «cash in» voice chime
 * (public/sounds/order-cash.ogg) so the phone notification stands out.
 */

import { ORDER_CASH_SOUND_OGG_BASE64 } from "../lib/orderCashSoundData.js";
import { buildOrderCard, buildOrderKeyboard, formatIls } from "../lib/telegramOrderCard.js";

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

export function telegramConfig() {
  const token = String(process.env.TELEGRAM_BOT_TOKEN || "").trim();
  const chatId = String(process.env.TELEGRAM_CHAT_ID || "").trim();
  const threadRaw = String(process.env.TELEGRAM_MESSAGE_THREAD_ID || "").trim();
  const threadId = threadRaw && /^\d+$/.test(threadRaw) ? Number(threadRaw) : undefined;
  return { token, chatId, threadId };
}

export async function telegramApi(method, payload) {
  const { token } = telegramConfig();
  if (!token) {
    return { ok: false, status: 503, data: { ok: false, error: "telegram_not_configured" } };
  }
  let res;
  try {
    res = await fetch(`https://api.telegram.org/bot${token}/${method}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch {
    return { ok: false, status: 502, data: { ok: false, error: "telegram_unreachable" } };
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok || !data.ok) {
    return {
      ok: false,
      status: 502,
      data: {
        ok: false,
        error: "telegram_rejected",
        detail: data.description || res.statusText,
      },
    };
  }
  return { ok: true, status: 200, data };
}

async function telegramApiForm(method, formData) {
  const { token } = telegramConfig();
  if (!token) {
    return { ok: false, status: 503, data: { ok: false, error: "telegram_not_configured" } };
  }
  let res;
  try {
    res = await fetch(`https://api.telegram.org/bot${token}/${method}`, {
      method: "POST",
      body: formData,
    });
  } catch {
    return { ok: false, status: 502, data: { ok: false, error: "telegram_unreachable" } };
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok || !data.ok) {
    return {
      ok: false,
      status: 502,
      data: {
        ok: false,
        error: "telegram_rejected",
        detail: data.description || res.statusText,
      },
    };
  }
  return { ok: true, status: 200, data };
}

function readCashSound() {
  try {
    if (!ORDER_CASH_SOUND_OGG_BASE64) return null;
    return Buffer.from(ORDER_CASH_SOUND_OGG_BASE64, "base64");
  } catch {
    return null;
  }
}

/** Short cha-ching voice so the phone alert feels like money coming in. */
export async function sendOrderCashSound(order = {}) {
  const { chatId, threadId } = telegramConfig();
  if (!chatId) return { ok: false, skipped: true, reason: "no_chat" };
  const buf = readCashSound();
  if (!buf?.length) return { ok: false, skipped: true, reason: "no_sound_file" };

  const number = String(order.number || order.orderNumber || "").trim();
  const total = order.total;
  const caption = [
    "💰 נכנס כסף!",
    number ? `#${number}` : null,
    Number.isFinite(Number(total)) ? formatIls(total) : null,
  ]
    .filter(Boolean)
    .join(" · ");

  const form = new FormData();
  form.append("chat_id", chatId);
  form.append("voice", new Blob([buf], { type: "audio/ogg" }), "order-cash.ogg");
  form.append("caption", caption);
  form.append("disable_notification", "false");
  if (threadId) form.append("message_thread_id", String(threadId));

  return telegramApiForm("sendVoice", form);
}

export async function sendOrderCard(order, opts = {}) {
  const { chatId, threadId } = telegramConfig();
  if (!chatId) {
    return {
      ok: false,
      status: 503,
      body: {
        ok: false,
        error: "telegram_not_configured",
        missing: {
          TELEGRAM_BOT_TOKEN: !telegramConfig().token,
          TELEGRAM_CHAT_ID: true,
        },
      },
    };
  }

  const card = buildOrderCard(order, opts);
  const reply_markup = buildOrderKeyboard(order, { status: card.status });
  const payload = {
    chat_id: chatId,
    text: card.text,
    parse_mode: "HTML",
    disable_web_page_preview: true,
    disable_notification: false,
  };
  if (reply_markup) payload.reply_markup = reply_markup;
  if (threadId) payload.message_thread_id = threadId;

  const result = await telegramApi("sendMessage", payload);
  if (!result.ok) {
    return { ok: false, status: result.status, body: result.data };
  }

  // Fire-and-forget cash chime — never fail the order card if sound fails.
  const sound = await sendOrderCashSound(order).catch(() => ({ ok: false }));

  return {
    ok: true,
    status: 200,
    body: {
      ok: true,
      message_id: result.data.result?.message_id,
      cash_sound: Boolean(sound?.ok),
    },
  };
}

export async function editOrderCard(chatId, messageId, order, opts = {}) {
  const card = buildOrderCard(order, opts);
  const reply_markup = buildOrderKeyboard(order, { status: card.status });
  const payload = {
    chat_id: chatId,
    message_id: messageId,
    text: card.text,
    parse_mode: "HTML",
    disable_web_page_preview: true,
  };
  if (reply_markup) payload.reply_markup = reply_markup;
  else payload.reply_markup = { inline_keyboard: [] };

  const result = await telegramApi("editMessageText", payload);
  return result;
}

export default async function handler(req, res) {
  res.setHeader("Cache-Control", "no-store");

  if (req.method === "OPTIONS") {
    res.statusCode = 204;
    res.end();
    return;
  }

  if (req.method === "GET") {
    const url = new URL(req.url || "/", "http://localhost");
    if (url.searchParams.get("test") !== "1") {
      sendJson(res, 405, { ok: false, error: "method_not_allowed" });
      return;
    }
    const sample = {
      number: "BRB-TEST",
      createdAt: new Date().toISOString(),
      payment: "bit",
      details: {
        name: "בדיקת מערכת",
        phone: "0540000000",
        email: "test@barbero.co.il",
        address: "רחוב לדוגמה 1",
        unit: "דירה 2",
        city: "תל אביב",
        postal: "6100000",
        notes: "הודעת בדיקה — כרטיס בסגנון מינוקס",
      },
      lines: [{ name: "טרימר בדיקה", qty: 1, unitPrice: 500, lineTotal: 500 }],
      total: 500,
    };
    const result = await sendOrderCard(sample);
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

  const result = await sendOrderCard(order);
  sendJson(res, result.status, result.body);
}
