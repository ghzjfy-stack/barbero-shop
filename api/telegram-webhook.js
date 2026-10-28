/**
 * Telegram Bot webhook — inline button callbacks (approve / cancel / refresh).
 *
 * Setup (once, after deploy):
 *   curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook" \
 *     -d "url=https://www.barbero.co.il/api/telegram-webhook" \
 *     -d "secret_token=$TELEGRAM_WEBHOOK_SECRET" \
 *     -d "allowed_updates=[\"callback_query\"]"
 *
 * Env:
 *   TELEGRAM_BOT_TOKEN
 *   TELEGRAM_WEBHOOK_SECRET   — random string; must match setWebhook secret_token
 *   GOOGLE_SHEETS_WEBHOOK_URL (+ optional GOOGLE_SHEETS_WEBHOOK_SECRET)
 */

import { postAppsScript } from "../lib/appsScriptWebhook.js";
import { parseCallbackData, waitingStatusOf } from "../lib/telegramOrderCard.js";
import { editOrderCard, telegramApi, telegramConfig } from "./telegram-order.js";

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

function sheetsConfig() {
  const url = String(process.env.GOOGLE_SHEETS_WEBHOOK_URL || "").trim();
  const secret = String(process.env.GOOGLE_SHEETS_WEBHOOK_SECRET || "").trim();
  return { url, secret };
}

async function sheetsPost(payload) {
  const { url, secret } = sheetsConfig();
  if (!url) return { ok: false, error: "sheets_not_configured" };
  const body = { ...payload };
  if (secret) body.secret = secret;
  const result = await postAppsScript(url, body);
  if (!result.ok || result.data?.ok === false || !result.data?.order) {
    return { ok: false, error: result.data?.error || "order_not_found" };
  }
  return { ok: true, order: result.data.order };
}

function sameStatus(order, status) {
  return String(order?.status || "").trim() === String(status || "").trim();
}

function grabCardField(text, label) {
  const m = String(text || "").match(new RegExp(`${label}\\s*:\\s*(.+)`, "m"));
  const value = m ? String(m[1] || "").trim() : "";
  return !value || value === "—" ? "" : value;
}

/** Rebuild order fields from the Telegram card when Sheets track is thin. */
function orderFromTelegramMessage(message, orderNumber) {
  const text = String(message?.text || "");
  const totalRaw = grabCardField(text, "סכום").replace(/[^\d.]/g, "");
  return {
    orderNumber,
    number: orderNumber,
    status: grabCardField(text, "סטטוס"),
    name: grabCardField(text, "לקוח"),
    email: grabCardField(text, "אימייל"),
    phone: grabCardField(text, "טלפון"),
    items: grabCardField(text, "מוצר"),
    total: totalRaw ? Number(totalRaw) : "",
    address: grabCardField(text, "כתובת"),
    unit: grabCardField(text, "קומה/דירה"),
    notes: grabCardField(text, "הערות"),
    createdAt: grabCardField(text, "נוצרה"),
    payment: "ביט",
  };
}

function mergeOrder(...parts) {
  const out = {};
  for (const part of parts) {
    if (!part || typeof part !== "object") continue;
    for (const [key, value] of Object.entries(part)) {
      if (value == null) continue;
      const s = typeof value === "string" ? value.trim() : value;
      if (s === "" || s === "—") continue;
      out[key] = value;
    }
  }
  return out;
}

/** Live Apps Script reliably supports type:track (same as /api/track-order). */
async function sheetsGetOrder(orderNumber) {
  return sheetsPost({ type: "track", orderNumber });
}

async function sheetsAppendStatus(orderNumber, status, paid, prev = {}) {
  const { url, secret } = sheetsConfig();
  if (!url) return { ok: false, error: "sheets_not_configured" };
  const payload = {
    order: { number: orderNumber },
    row: {
      orderNumber,
      status,
      paid: paid || (status === "שולם" ? "Yes" : "No"),
      createdAt: prev.createdAt || "",
      name: prev.name || "",
      phone: prev.phone || "",
      email: prev.email || "",
      city: prev.city || "",
      items: prev.items || "",
      payment: prev.payment || "ביט",
      // Empty total so סיכומים SUM does not double the original row.
      total: "",
      notes: "עדכון סטטוס מטלגרם",
    },
  };
  if (secret) payload.secret = secret;
  const result = await postAppsScript(url, payload);
  if (!result.ok || result.data?.ok === false) {
    return { ok: false, error: result.data?.error || "append_failed" };
  }
  const tracked = await sheetsGetOrder(orderNumber);
  const order = {
    ...prev,
    ...(tracked.order || {}),
    orderNumber,
    status,
    total: tracked.order?.total || prev.total,
    name: tracked.order?.name || prev.name,
    phone: tracked.order?.phone || prev.phone,
    email: tracked.order?.email || prev.email,
    items: tracked.order?.items || prev.items,
    payment: tracked.order?.payment || prev.payment,
  };
  if (tracked.ok && sameStatus(tracked.order, status)) {
    return { ok: true, order };
  }
  if (result.data?.ok) {
    return { ok: true, order };
  }
  return { ok: false, error: tracked.error || "status_not_supported", order };
}

async function sheetsSetStatus(orderNumber, status, prev = {}) {
  const paid = status === "שולם" ? "Yes" : status === "בוטל" ? "No" : undefined;
  const viaStatus = await sheetsPost({ type: "status", orderNumber, status, paid });
  if (viaStatus.ok && sameStatus(viaStatus.order, status)) return viaStatus;
  const viaTrack = await sheetsPost({ type: "track", orderNumber, setStatus: status, paid });
  if (viaTrack.ok && sameStatus(viaTrack.order, status)) return viaTrack;
  const exists = await sheetsPost({ type: "track", orderNumber });
  const seed = mergeOrder(prev, exists.ok ? exists.order : null, { orderNumber, status });
  if (exists.ok || prev.name || prev.items || prev.phone) {
    return sheetsAppendStatus(orderNumber, status, paid, seed);
  }
  return { ok: false, error: viaStatus.error || viaTrack.error || "order_not_found" };
}

async function answerCallback(callbackQueryId, text, alert = false) {
  return telegramApi("answerCallbackQuery", {
    callback_query_id: callbackQueryId,
    text: String(text || "").slice(0, 180),
    show_alert: Boolean(alert),
  });
}

function actorName(from = {}) {
  return [from.first_name, from.last_name].filter(Boolean).join(" ") || from.username || "מישהו";
}

async function announceAction(chatId, threadId, text) {
  const payload = {
    chat_id: chatId,
    text,
    disable_notification: true,
  };
  if (threadId) payload.message_thread_id = threadId;
  return telegramApi("sendMessage", payload);
}

function toCardOrder(sheetOrder) {
  return {
    number: sheetOrder.orderNumber || sheetOrder.number,
    orderNumber: sheetOrder.orderNumber || sheetOrder.number,
    status: sheetOrder.status,
    payment: sheetOrder.payment,
    total: sheetOrder.total,
    createdAt: sheetOrder.createdAt,
    itemsText: sheetOrder.items,
    details: {
      name: sheetOrder.name,
      phone: sheetOrder.phone,
      email: sheetOrder.email,
      address: sheetOrder.address,
      city: sheetOrder.city,
      postal: sheetOrder.postal,
      unit: sheetOrder.unit,
      notes: sheetOrder.notes,
    },
    name: sheetOrder.name,
    phone: sheetOrder.phone,
    email: sheetOrder.email,
    address: sheetOrder.address,
    city: sheetOrder.city,
    postal: sheetOrder.postal,
    unit: sheetOrder.unit,
    notes: sheetOrder.notes,
  };
}

export default async function handler(req, res) {
  res.setHeader("Cache-Control", "no-store");

  if (req.method === "GET") {
    sendJson(res, 200, {
      ok: true,
      service: "telegram-webhook",
      configured: Boolean(telegramConfig().token),
      rev: "card-merge",
    });
    return;
  }

  if (req.method !== "POST") {
    sendJson(res, 405, { ok: false, error: "method_not_allowed" });
    return;
  }

  const expectedSecret = String(process.env.TELEGRAM_WEBHOOK_SECRET || "").trim();
  if (expectedSecret) {
    const got = String(req.headers["x-telegram-bot-api-secret-token"] || "");
    if (got !== expectedSecret) {
      sendJson(res, 401, { ok: false, error: "unauthorized" });
      return;
    }
  }

  let update;
  try {
    update = await readJson(req);
  } catch {
    sendJson(res, 400, { ok: false, error: "invalid_json" });
    return;
  }

  const cq = update?.callback_query;
  if (!cq?.id || !cq.data) {
    // Ignore plain messages — always 200 so Telegram stops retrying
    sendJson(res, 200, { ok: true, ignored: true });
    return;
  }

  const parsed = parseCallbackData(cq.data);
  if (!parsed) {
    await answerCallback(cq.id, "פעולה לא מזוהה");
    sendJson(res, 200, { ok: true });
    return;
  }

  const chatId = cq.message?.chat?.id;
  const messageId = cq.message?.message_id;
  const threadId = cq.message?.message_thread_id;
  const who = actorName(cq.from);

  try {
    if (parsed.action === "approve" || parsed.action === "cancel") {
      const nextStatus = parsed.action === "approve" ? "שולם" : "בוטל";
      const fromMsg = orderFromTelegramMessage(cq.message, parsed.orderNumber);
      const updated = await sheetsSetStatus(parsed.orderNumber, nextStatus, fromMsg);
      const cardOrder = toCardOrder(
        mergeOrder(fromMsg, updated.order, {
          orderNumber: parsed.orderNumber,
          status: nextStatus,
        }),
      );
      if (chatId && messageId) {
        await editOrderCard(chatId, messageId, cardOrder, { status: nextStatus });
      }
      if (!updated.ok) {
        await answerCallback(cq.id, "הכרטיס עודכן. לא הצלחתי לכתוב לשיטס", true);
        sendJson(res, 200, { ok: false, error: updated.error, status: nextStatus });
        return;
      }
      const mark = parsed.action === "approve" ? "✅" : "❌";
      const label = parsed.action === "approve" ? "אשר" : "בטל";
      if (chatId) {
        await announceAction(
          chatId,
          threadId,
          `BARBERO Orders: ${who}: ${mark} ${label} #${parsed.orderNumber}`,
        );
      }
      await answerCallback(cq.id, `${label} #${parsed.orderNumber}`);
      sendJson(res, 200, { ok: true, status: nextStatus });
      return;
    }

    if (parsed.action === "refresh") {
      const fromMsg = orderFromTelegramMessage(cq.message, parsed.orderNumber);
      const got = await sheetsGetOrder(parsed.orderNumber);
      const cardOrder = toCardOrder(
        mergeOrder(fromMsg, got.ok ? got.order : null, { orderNumber: parsed.orderNumber }),
      );
      if (chatId && messageId) {
        await editOrderCard(chatId, messageId, cardOrder, {
          status: cardOrder.status || waitingStatusOf(cardOrder.payment),
        });
      }
      if (!got.ok && !fromMsg.name && !fromMsg.items) {
        await answerCallback(cq.id, "לא מצאתי את ההזמנה לרענון", true);
        sendJson(res, 200, { ok: false, error: got.error });
        return;
      }
      await answerCallback(cq.id, "כרטיס עודכן");
      sendJson(res, 200, { ok: true, refreshed: true });
      return;
    }

    await answerCallback(cq.id, "OK");
    sendJson(res, 200, { ok: true });
  } catch (error) {
    await answerCallback(cq.id, "שגיאה זמנית — נסו שוב", true).catch(() => {});
    sendJson(res, 200, { ok: false, error: error?.message || String(error) });
  }
}
