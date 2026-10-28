/**
 * POST /api/track-order — look up an order status in Google Sheets
 * via the Apps Script webhook (read-only track action).
 *
 * Body: { orderNumber?: "BRB-123456", phone?: "05…" }
 * At least one of orderNumber / phone is required.
 *
 * Vercel env: GOOGLE_SHEETS_WEBHOOK_URL (+ optional GOOGLE_SHEETS_WEBHOOK_SECRET)
 */

import { postAppsScript, safeWebhookHint, sheetsWebhookUrl } from "../lib/appsScriptWebhook.js";

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
  res.setHeader("Cache-Control", "no-store");
  res.end(JSON.stringify(body));
}

function normalizeOrderNumber(value) {
  return String(value || "")
    .trim()
    .toUpperCase();
}

function normalizePhone(value) {
  let digits = String(value || "").replace(/[^\d]/g, "");
  if (digits.startsWith("972") && digits.length >= 11) {
    digits = `0${digits.slice(3)}`;
  }
  if (digits.length > 9) digits = digits.slice(-9);
  return digits;
}

/** Customer-facing status copy + timeline step index. */
export function describeStatus(status) {
  const value = String(status || "").trim();
  const map = {
    "ממתין לביט": {
      headline: "ממתינים להשלמת התשלום בביט",
      detail: "אחרי התשלום נתחיל להכין את ההזמנה למשלוח.",
      step: 1,
      pendingPayment: true,
    },
    "ממתין ל-PayPal": {
      headline: "ממתינים להשלמת התשלום ב-PayPal",
      detail: "אחרי התשלום נתחיל להכין את ההזמנה למשלוח.",
      step: 1,
      pendingPayment: true,
    },
    שולם: {
      headline: "התשלום התקבל",
      detail: "ההזמנה עוברת להכנה למשלוח.",
      step: 2,
    },
    בהכנה: {
      headline: "ההזמנה בהכנה",
      detail: "אנחנו מכינים את החבילה לפני שליחה מארה״ב.",
      step: 2,
    },
    "משלוח מארה״ב": {
      headline: "החבילה בדרך מארה״ב",
      detail: "המשלוח בדרך לישראל. זמן אספקה משוער: 7–14 ימי עסקים.",
      step: 3,
    },
    נמסר: {
      headline: "ההזמנה נמסרה",
      detail: "תודה שבחרתם ב־BARBERO.",
      step: 4,
    },
    בוטל: {
      headline: "ההזמנה בוטלה",
      detail: "לשאלות אפשר לפנות אלינו בוואטסאפ או במייל.",
      step: -1,
      cancelled: true,
    },
  };
  return (
    map[value] || {
      headline: value || "ההזמנה בטיפול",
      detail: "לעדכון מדויק אפשר לפנות אלינו בוואטסאפ.",
      step: 0,
    }
  );
}

export function buildTimeline(status) {
  const info = describeStatus(status);
  const labels = [
    "ההזמנה התקבלה",
    "תשלום",
    "הכנה למשלוח",
    "בדרך מארה״ב",
    "נמסר",
  ];
  if (info.cancelled) {
    return labels.map((label, index) => ({
      id: index,
      label: index === 0 ? label : index === 1 ? "בוטלה" : label,
      state: index === 0 ? "done" : index === 1 ? "current" : "todo",
    }));
  }
  const current = Math.max(0, Math.min(info.step, labels.length - 1));
  return labels.map((label, index) => ({
    id: index,
    label:
      index === 1 && info.pendingPayment
        ? "ממתין לתשלום"
        : index === 1
          ? "שולם"
          : label,
    state: index < current ? "done" : index === current ? "current" : "todo",
  }));
}

export default async function handler(req, res) {
  if (req.method === "OPTIONS") {
    res.statusCode = 204;
    res.end();
    return;
  }

  const webhook = sheetsWebhookUrl();

  if (req.method === "GET") {
    sendJson(res, 200, {
      ok: true,
      configured: Boolean(webhook),
      webhookHost: webhook ? safeWebhookHint(webhook) : null,
      hint: "POST { orderNumber? , phone? } to look up order status",
    });
    return;
  }

  if (req.method !== "POST") {
    sendJson(res, 405, { ok: false, error: "method_not_allowed" });
    return;
  }

  if (!webhook) {
    sendJson(res, 503, {
      ok: false,
      error: "sheets_not_configured",
      missing: { GOOGLE_SHEETS_WEBHOOK_URL: true },
    });
    return;
  }

  let body;
  try {
    body = await readJson(req);
  } catch {
    sendJson(res, 400, { ok: false, error: "invalid_json" });
    return;
  }

  const orderNumber = normalizeOrderNumber(body?.orderNumber || body?.o);
  const phone = normalizePhone(body?.phone || body?.p);

  if (!orderNumber && phone.length < 9) {
    sendJson(res, 400, {
      ok: false,
      error: "missing_query",
      hint: "Provide orderNumber (BRB-…) and/or a valid phone",
    });
    return;
  }

  const secret = String(process.env.GOOGLE_SHEETS_WEBHOOK_SECRET || "").trim();
  const payload = {
    type: "track",
    secret: secret || undefined,
    orderNumber: orderNumber || undefined,
    phone: phone || undefined,
  };

  let result;
  try {
    result = await postAppsScript(webhook, payload);
  } catch {
    sendJson(res, 502, { ok: false, error: "sheets_unreachable" });
    return;
  }

  if (!result.ok) {
    const detail = result.data?.error || result.data?.raw || result.statusText;
    const html = typeof detail === "string" && detail.includes("<!DOCTYPE html");
    sendJson(res, 502, {
      ok: false,
      error: "sheets_rejected",
      detail: html ? "apps_script_returned_html" : detail,
      hint: html
        ? "Redeploy the Apps Script Web App after pasting the latest barbero-orders.gs (track support)."
        : undefined,
      webhookHost: safeWebhookHint(webhook),
    });
    return;
  }

  if (result.data?.ok === false || !result.data?.order) {
    sendJson(res, 404, {
      ok: false,
      error: result.data?.error || "not_found",
    });
    return;
  }

  const order = result.data.order;
  const statusInfo = describeStatus(order.status);
  const timeline = buildTimeline(order.status);
  const shipDays =
    order.shipDays == null || Number.isNaN(Number(order.shipDays))
      ? null
      : Number(order.shipDays);

  sendJson(res, 200, {
    ok: true,
    order: {
      number: order.orderNumber,
      status: order.status,
      createdAt: order.createdAt || "",
      city: order.city || "",
      items: order.items || "",
      payment: order.payment || "",
      shipDays,
      headline: statusInfo.headline,
      detail:
        order.status === "משלוח מארה״ב" && shipDays != null
          ? `החבילה בדרך כ־${shipDays} ימים. זמן אספקה משוער: 7–14 ימי עסקים.`
          : statusInfo.detail,
      timeline,
    },
    matchCount: result.data.matchCount || 1,
  });
}
