/**
 * Telegram Bot webhook — orders control menu + status sync.
 *
 * Setup (after deploy):
 *   curl -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook" \
 *     -d "url=https://www.barbero.co.il/api/telegram-webhook" \
 *     -d "secret_token=$TELEGRAM_WEBHOOK_SECRET" \
 *     -d 'allowed_updates=["callback_query","message"]'
 *   curl "https://www.barbero.co.il/api/telegram-webhook?setup=1"
 *
 * Env:
 *   TELEGRAM_BOT_TOKEN
 *   TELEGRAM_WEBHOOK_SECRET
 *   TELEGRAM_CHAT_ID
 *   GOOGLE_SHEETS_WEBHOOK_URL (+ optional secret)
 *   SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY
 */

import { postAppsScript, sheetsWebhookUrl } from "../lib/appsScriptWebhook.js";
import { getSupabaseAdmin } from "../lib/supabaseAdmin.js";
import {
  countOrdersByFilter,
  getOrderByNumber,
  listOrders,
  setOrderStatus,
  supabaseRowToCardOrder,
} from "../lib/supabaseOrders.js";
import { waitingStatusOf } from "../lib/telegramOrderCard.js";
import {
  buildMainMenuKeyboard,
  buildMainMenuText,
  buildOrdersListKeyboard,
  buildOrdersListText,
  buildReplyMenuKeyboard,
  parseMenuCallback,
  parseTextCommand,
} from "../lib/telegramOrdersMenu.js";
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
  const url = sheetsWebhookUrl();
  const secret = String(process.env.GOOGLE_SHEETS_WEBHOOK_SECRET || "").trim();
  return { url, secret };
}

async function sheetsPost(payload) {
  const { url, secret } = sheetsConfig();
  if (!url) return { ok: false, error: "sheets_not_configured" };
  const body = { ...payload };
  if (secret) body.secret = secret;
  const result = await postAppsScript(url, body);
  if (!result.ok || result.data?.ok === false) {
    return { ok: false, error: result.data?.error || "sheets_error", data: result.data };
  }
  return { ok: true, ...(result.data || {}) };
}

function sameStatus(order, status) {
  return String(order?.status || "").trim() === String(status || "").trim();
}

function grabCardField(text, label) {
  const m = String(text || "").match(new RegExp(`${label}\\s*:\\s*(.+)`, "m"));
  const value = m ? String(m[1] || "").trim() : "";
  return !value || value === "—" ? "" : value;
}

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

async function sheetsGetOrder(orderNumber) {
  const result = await sheetsPost({ type: "track", orderNumber });
  if (!result.ok || !result.order) return { ok: false, error: result.error || "order_not_found" };
  return { ok: true, order: result.order };
}

async function sheetsListOrders(filter, limit = 10) {
  const result = await sheetsPost({ type: "list", filter, limit });
  if (!result.ok) return { ok: false, error: result.error || "list_failed", orders: [] };
  return { ok: true, orders: Array.isArray(result.orders) ? result.orders : [] };
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
  if (tracked.ok && sameStatus(tracked.order, status)) return { ok: true, order };
  if (result.data?.ok) return { ok: true, order };
  return { ok: false, error: tracked.error || "status_not_supported", order };
}

async function sheetsSetStatus(orderNumber, status, prev = {}) {
  const paid =
    status === "שולם" || status === "בהכנה" || status === "משלוח מארה״ב" || status === "נמסר"
      ? "Yes"
      : status === "בוטל"
        ? "No"
        : undefined;
  const viaStatus = await sheetsPost({ type: "status", orderNumber, status, paid });
  if (viaStatus.ok && viaStatus.order && sameStatus(viaStatus.order, status)) {
    return { ok: true, order: viaStatus.order };
  }
  const viaTrack = await sheetsPost({ type: "track", orderNumber, setStatus: status, paid });
  if (viaTrack.ok && viaTrack.order && sameStatus(viaTrack.order, status)) {
    return { ok: true, order: viaTrack.order };
  }
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
    items: sheetOrder.items,
  };
}

function isAuthorizedChat(chatId) {
  const configured = String(telegramConfig().chatId || "").trim();
  if (!configured) return true;
  return String(chatId) === configured;
}

async function sendHtml(chatId, text, replyMarkup, threadId) {
  const payload = {
    chat_id: chatId,
    text,
    parse_mode: "HTML",
    disable_web_page_preview: true,
  };
  if (replyMarkup) payload.reply_markup = replyMarkup;
  if (threadId) payload.message_thread_id = threadId;
  return telegramApi("sendMessage", payload);
}

async function editHtml(chatId, messageId, text, replyMarkup) {
  const payload = {
    chat_id: chatId,
    message_id: messageId,
    text,
    parse_mode: "HTML",
    disable_web_page_preview: true,
  };
  if (replyMarkup) payload.reply_markup = replyMarkup;
  return telegramApi("editMessageText", payload);
}

async function loadOrderBundle(orderNumber, fromMsg = {}) {
  const [sheets, supabase] = await Promise.all([
    sheetsGetOrder(orderNumber),
    getOrderByNumber(orderNumber),
  ]);
  const fromSupabase = supabase.ok ? supabaseRowToCardOrder(supabase.order) : null;
  const merged = mergeOrder(
    fromMsg,
    sheets.ok ? sheets.order : null,
    fromSupabase
      ? {
          orderNumber: fromSupabase.orderNumber,
          status: fromSupabase.status,
          payment: fromSupabase.payment,
          total: fromSupabase.total,
          name: fromSupabase.name,
          phone: fromSupabase.phone,
          email: fromSupabase.email,
          city: fromSupabase.city,
          address: fromSupabase.address,
          unit: fromSupabase.unit,
          postal: fromSupabase.postal,
          notes: fromSupabase.notes,
          items: fromSupabase.items,
          createdAt: fromSupabase.createdAt,
        }
      : null,
    { orderNumber },
  );
  return {
    sheets,
    supabase,
    cardOrder: toCardOrder(merged),
    found: Boolean(sheets.ok || supabase.ok || fromMsg.name || fromMsg.items),
  };
}

async function loadOrdersList(filter) {
  const supabase = await listOrders({ filter, limit: 10 });
  if (supabase.ok && supabase.orders.length) {
    return { ok: true, source: "supabase", orders: supabase.orders };
  }
  const sheets = await sheetsListOrders(filter, 10);
  if (sheets.ok) {
    return {
      ok: true,
      source: "sheets",
      orders: sheets.orders.map((row) => toCardOrder(row)),
    };
  }
  return {
    ok: false,
    source: null,
    orders: [],
    error: supabase.error || sheets.error || "list_failed",
  };
}

async function buildHealthReport() {
  const sheetsUrl = Boolean(sheetsWebhookUrl());
  const { client: supabaseClient } = getSupabaseAdmin();
  const tg = telegramConfig();
  let sheetsOk = false;
  let sheetsDetail = sheetsUrl ? "not_checked" : "missing_env";
  if (sheetsUrl) {
    const ping = await sheetsPost({ type: "list", filter: "all", limit: 1 });
    sheetsOk = ping.ok;
    sheetsDetail = ping.ok ? "ok" : ping.error || "error";
  }
  let supabaseOk = false;
  let supabaseDetail = supabaseClient ? "not_checked" : "missing_env";
  if (supabaseClient) {
    const listed = await listOrders({ filter: "all", limit: 1 });
    supabaseOk = listed.ok;
    supabaseDetail = listed.ok ? `ok (${listed.orders.length} sample)` : listed.error || "error";
  }
  const lines = [
    "🩺 <b>בדיקת סנכרון BARBERO</b>",
    "",
    `${tg.token ? "✅" : "❌"} Telegram bot token`,
    `${tg.chatId ? "✅" : "❌"} TELEGRAM_CHAT_ID`,
    `${sheetsOk ? "✅" : "❌"} Google Sheets (${sheetsDetail})`,
    `${supabaseOk ? "✅" : "❌"} Supabase orders (${supabaseDetail})`,
    "",
    sheetsOk && supabaseOk
      ? "הכל מחובר — הזמנות חדשות + כפתורי סטטוס מסתנכרנים."
      : "יש חסרים — בדקו Vercel env + הרצת supabase/schema.sql + Deploy לשיטס.",
  ];
  return {
    text: lines.join("\n"),
    ok: Boolean(tg.token && tg.chatId && sheetsOk && supabaseOk),
  };
}

async function ensureBotCommands() {
  return telegramApi("setMyCommands", {
    commands: [
      { command: "menu", description: "תפריט ניהול הזמנות" },
      { command: "orders", description: "הזמנות אחרונות" },
      { command: "wait", description: "ממתינים לתשלום" },
      { command: "paid", description: "הזמנות ששולמו" },
      { command: "ship", description: "במשלוח" },
      { command: "health", description: "בדיקת סנכרון Sheets/Supabase" },
    ],
  });
}

async function showMainMenu(chatId, threadId, { editMessageId } = {}) {
  const counted = await countOrdersByFilter();
  const counts = counted.ok ? counted.counts : {};
  const text = buildMainMenuText(counts);
  const keyboard = buildMainMenuKeyboard(counts);
  if (editMessageId) {
    return editHtml(chatId, editMessageId, text, keyboard);
  }
  await sendHtml(chatId, text, keyboard, threadId);
  // Persistent reply keyboard for quick access
  await sendHtml(chatId, "קיצורי מקלדת פעילים ✅", buildReplyMenuKeyboard(), threadId);
  return { ok: true };
}

async function showOrdersList(chatId, threadId, filter, { editMessageId } = {}) {
  const listed = await loadOrdersList(filter);
  const text = buildOrdersListText(filter, listed.orders);
  const keyboard = buildOrdersListKeyboard(filter, listed.orders);
  if (editMessageId) return editHtml(chatId, editMessageId, text, keyboard);
  return sendHtml(chatId, text, keyboard, threadId);
}

async function openOrderCard(chatId, threadId, orderNumber, fromMsg = {}, { editMessageId } = {}) {
  const bundle = await loadOrderBundle(orderNumber, fromMsg);
  if (!bundle.found) {
    const text = `לא מצאתי הזמנה <b>#${orderNumber}</b> בשיטס/Supabase.`;
    if (editMessageId) return editHtml(chatId, editMessageId, text, buildMainMenuKeyboard());
    return sendHtml(chatId, text, buildMainMenuKeyboard(), threadId);
  }
  if (editMessageId) {
    return editOrderCard(chatId, editMessageId, bundle.cardOrder, {
      status: bundle.cardOrder.status || waitingStatusOf(bundle.cardOrder.payment),
    });
  }
  const { buildOrderCard, buildOrderKeyboard } = await import("../lib/telegramOrderCard.js");
  const card = buildOrderCard(bundle.cardOrder);
  return sendHtml(
    chatId,
    card.text,
    buildOrderKeyboard(bundle.cardOrder, { status: card.status }),
    threadId,
  );
}

async function applyStatusChange({ orderNumber, status, fromMsg, chatId, messageId, threadId, who, callbackId }) {
  const paid =
    status === "שולם" || status === "בהכנה" || status === "משלוח מארה״ב" || status === "נמסר"
      ? "Yes"
      : status === "בוטל"
        ? "No"
        : undefined;
  const [updated, supabase] = await Promise.all([
    sheetsSetStatus(orderNumber, status, fromMsg),
    setOrderStatus(orderNumber, status, { ...fromMsg, paid }),
  ]);
  const cardOrder = toCardOrder(
    mergeOrder(fromMsg, updated.order, {
      orderNumber,
      status,
    }),
  );
  if (chatId && messageId) {
    await editOrderCard(chatId, messageId, cardOrder, { status });
  }
  if (!updated.ok && !supabase.ok) {
    await answerCallback(callbackId, "הכרטיס עודכן. סנכרון שיטס/Supabase נכשל", true);
    return {
      ok: false,
      error: updated.error || supabase.error,
      status,
      sheets: updated,
      supabase,
    };
  }
  if (chatId) {
    const syncNote =
      updated.ok && supabase.ok
        ? ""
        : updated.ok
          ? " (שיטס OK · Supabase חלקי)"
          : " (Supabase OK · שיטס חלקי)";
    await announceAction(chatId, threadId, `BARBERO Orders: ${who}: ${status} #${orderNumber}${syncNote}`);
  }
  await answerCallback(callbackId, `${status} #${orderNumber}`);
  return {
    ok: true,
    status,
    sheets: { ok: updated.ok, error: updated.error },
    supabase: { ok: supabase.ok, error: supabase.error, order: supabase.order },
  };
}

export default async function handler(req, res) {
  res.setHeader("Cache-Control", "no-store");

  if (req.method === "GET") {
    const url = new URL(req.url || "/", "http://localhost");
    if (url.searchParams.get("setup") === "1") {
      const commands = await ensureBotCommands();
      sendJson(res, 200, {
        ok: true,
        service: "telegram-webhook",
        setup: commands.data || commands,
        hint: "Also re-run setWebhook with allowed_updates including message + callback_query",
      });
      return;
    }
    sendJson(res, 200, {
      ok: true,
      service: "telegram-webhook",
      configured: Boolean(telegramConfig().token),
      rev: "orders-control-menu",
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

  try {
    // ----- text commands / reply keyboard -----
    const message = update?.message;
    if (message?.chat?.id && message.text) {
      const chatId = message.chat.id;
      const threadId = message.message_thread_id;
      if (message.chat.type !== "private" && !isAuthorizedChat(chatId)) {
        sendJson(res, 200, { ok: true, ignored: "foreign_chat" });
        return;
      }
      const cmd = parseTextCommand(message.text);
      if (!cmd) {
        sendJson(res, 200, { ok: true, ignored: true });
        return;
      }
      if (cmd.action === "home") {
        await showMainMenu(chatId, threadId);
        sendJson(res, 200, { ok: true, menu: true });
        return;
      }
      if (cmd.action === "health") {
        const report = await buildHealthReport();
        await sendHtml(chatId, report.text, buildMainMenuKeyboard(), threadId);
        sendJson(res, 200, { ok: true, health: report.ok });
        return;
      }
      if (cmd.action === "list") {
        await showOrdersList(chatId, threadId, cmd.filter || "all");
        sendJson(res, 200, { ok: true, list: cmd.filter || "all" });
        return;
      }
      if (cmd.action === "open") {
        await openOrderCard(chatId, threadId, cmd.orderNumber);
        sendJson(res, 200, { ok: true, opened: cmd.orderNumber });
        return;
      }
      sendJson(res, 200, { ok: true, ignored: true });
      return;
    }

    // ----- inline callbacks -----
    const cq = update?.callback_query;
    if (!cq?.id || !cq.data) {
      sendJson(res, 200, { ok: true, ignored: true });
      return;
    }

    const parsed = parseMenuCallback(cq.data);
    if (!parsed) {
      await answerCallback(cq.id, "פעולה לא מזוהה");
      sendJson(res, 200, { ok: true });
      return;
    }

    const chatId = cq.message?.chat?.id;
    const messageId = cq.message?.message_id;
    const threadId = cq.message?.message_thread_id;
    const who = actorName(cq.from);

    if (cq.message?.chat?.type !== "private" && chatId && !isAuthorizedChat(chatId)) {
      await answerCallback(cq.id, "אין הרשאה בצ׳אט הזה", true);
      sendJson(res, 200, { ok: false, error: "unauthorized_chat" });
      return;
    }

    if (parsed.kind === "menu" && parsed.action === "home") {
      await showMainMenu(chatId, threadId, { editMessageId: messageId });
      await answerCallback(cq.id, "תפריט");
      sendJson(res, 200, { ok: true, menu: true });
      return;
    }

    if (parsed.kind === "menu" && parsed.action === "health") {
      const report = await buildHealthReport();
      if (chatId && messageId) await editHtml(chatId, messageId, report.text, buildMainMenuKeyboard());
      else if (chatId) await sendHtml(chatId, report.text, buildMainMenuKeyboard(), threadId);
      await answerCallback(cq.id, report.ok ? "הכל מחובר" : "יש חסרים");
      sendJson(res, 200, { ok: true, health: report.ok });
      return;
    }

    if (parsed.kind === "menu" && parsed.action === "list") {
      await showOrdersList(chatId, threadId, parsed.filter || "all", { editMessageId: messageId });
      await answerCallback(cq.id, "רשימה");
      sendJson(res, 200, { ok: true, list: parsed.filter });
      return;
    }

    if (parsed.kind === "order" && parsed.action === "open") {
      const fromMsg = orderFromTelegramMessage(cq.message, parsed.orderNumber);
      await openOrderCard(chatId, threadId, parsed.orderNumber, fromMsg, {
        editMessageId: messageId,
      });
      await answerCallback(cq.id, `#${parsed.orderNumber}`);
      sendJson(res, 200, { ok: true, opened: parsed.orderNumber });
      return;
    }

    if (parsed.kind === "order" && parsed.action === "setStatus") {
      const fromMsg = orderFromTelegramMessage(cq.message, parsed.orderNumber);
      const result = await applyStatusChange({
        orderNumber: parsed.orderNumber,
        status: parsed.status,
        fromMsg,
        chatId,
        messageId,
        threadId,
        who,
        callbackId: cq.id,
      });
      sendJson(res, 200, result);
      return;
    }

    if (parsed.kind === "order" && parsed.action === "refresh") {
      const fromMsg = orderFromTelegramMessage(cq.message, parsed.orderNumber);
      const bundle = await loadOrderBundle(parsed.orderNumber, fromMsg);
      if (chatId && messageId) {
        await editOrderCard(chatId, messageId, bundle.cardOrder, {
          status: bundle.cardOrder.status || waitingStatusOf(bundle.cardOrder.payment),
        });
      }
      if (!bundle.found) {
        await answerCallback(cq.id, "לא מצאתי את ההזמנה לרענון", true);
        sendJson(res, 200, { ok: false, error: "order_not_found" });
        return;
      }
      await answerCallback(cq.id, "כרטיס עודכן");
      sendJson(res, 200, {
        ok: true,
        refreshed: true,
        sheets: { ok: bundle.sheets.ok },
        supabase: { ok: bundle.supabase.ok },
      });
      return;
    }

    await answerCallback(cq.id, "OK");
    sendJson(res, 200, { ok: true });
  } catch (error) {
    if (update?.callback_query?.id) {
      await answerCallback(update.callback_query.id, "שגיאה זמנית — נסו שוב", true).catch(() => {});
    }
    sendJson(res, 200, { ok: false, error: error?.message || String(error) });
  }
}
