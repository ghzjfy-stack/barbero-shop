/**
 * POST /api/sheets-order — forward a checkout order to a Google Apps Script
 * web app that appends a row to the BARBERO orders Google Sheet.
 *
 * Vercel env:
 *   GOOGLE_SHEETS_WEBHOOK_URL     — Apps Script Web App URL (ends with /exec)
 *   GOOGLE_SHEETS_WEBHOOK_SECRET  — optional shared secret (must match the script)
 */

import { postAppsScript, safeWebhookHint, sheetsWebhookUrl } from "../lib/appsScriptWebhook.js";
import { upsertOrder } from "../lib/supabaseOrders.js";

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

function formatIls(amount) {
  const n = Number(amount);
  if (!Number.isFinite(n)) return "";
  return n;
}

function formatWhen(iso) {
  try {
    return new Intl.DateTimeFormat("he-IL", {
      timeZone: "Asia/Jerusalem",
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

function buildItemsText(lines = []) {
  if (!Array.isArray(lines) || lines.length === 0) return "";
  return lines
    .map((line) => {
      const qty = Number(line.qty) || 1;
      const label = line.label ? ` (${line.label})` : "";
      return `${line.name || "מוצר"}${label} ×${qty}`;
    })
    .join(" | ");
}

/** Flat row the Apps Script appends into the Minox-style sheet. */
export function buildSheetRow(order) {
  const details = order?.details || {};
  const payment = order?.payment === "paypal" ? "PayPal" : "ביט";
  const status = payment === "PayPal" ? "ממתין ל-PayPal" : "ממתין לביט";
  return {
    status,
    paid: "No",
    createdAt: formatWhen(order?.createdAt),
    orderNumber: order?.number || "",
    name: details.name || "",
    phone: details.phone || "",
    email: String(details.email || "").trim().toLowerCase(),
    city: details.city || "",
    address: details.address || "",
    unit: details.unit || "",
    postal: details.postal || "",
    notes: [
      details.notes || "",
      order?.coupon && order?.discount
        ? `קופון ${order.coupon}: −₪${order.discount}`
        : "",
    ]
      .filter(Boolean)
      .join(" · "),
    items: buildItemsText(order?.lines),
    // מחיר סופי ללקוח (אחרי קופון אם יש) — עלות מוצר/משלוח אמיתית ממלאים ידנית בשיטס
    total: formatIls(order?.total),
    productCost: "",
    shippingCost: "",
    payment,
  };
}

export default async function handler(req, res) {
  res.setHeader("Cache-Control", "no-store");

  if (req.method === "OPTIONS") {
    res.statusCode = 204;
    res.end();
    return;
  }

  const webhook = sheetsWebhookUrl();

  // Lightweight status check (no secrets): confirms env is set on this deployment.
  if (req.method === "GET") {
    sendJson(res, 200, {
      ok: true,
      configured: Boolean(webhook),
      webhookHost: webhook ? safeWebhookHint(webhook) : null,
      hint: webhook
        ? undefined
        : "Set GOOGLE_SHEETS_WEBHOOK_URL in Vercel → Production, then Redeploy",
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
      hint: "Set GOOGLE_SHEETS_WEBHOOK_URL in Vercel (Apps Script Web App URL), then Redeploy",
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

  const secret = String(process.env.GOOGLE_SHEETS_WEBHOOK_SECRET || "").trim();
  const payload = {
    secret: secret || undefined,
    row: buildSheetRow(order),
    order,
  };

  // Dual-write to Supabase so Sheets + DB stay aligned even if the browser
  // notifySupabaseOrder call is blocked.
  const supabasePromise = upsertOrder(order).catch((error) => ({
    ok: false,
    error: error?.message || String(error),
  }));

  let result;
  try {
    result = await postAppsScript(webhook, payload);
  } catch {
    const supabase = await supabasePromise;
    sendJson(res, 502, {
      ok: false,
      error: "sheets_unreachable",
      supabase: supabase?.ok ? { ok: true, order: supabase.order } : supabase,
    });
    return;
  }

  const supabase = await supabasePromise;

  if (!result.ok || result.data?.ok === false) {
    const detail = result.data?.error || result.data?.raw || result.statusText;
    const html = typeof detail === "string" && detail.includes("<!DOCTYPE html");
    sendJson(res, 502, {
      ok: false,
      error: "sheets_rejected",
      detail: html ? "apps_script_returned_html" : detail,
      hint: html
        ? "GOOGLE_SHEETS_WEBHOOK_URL is wrong or outdated. Set the current Web App /exec URL in Vercel Production and Redeploy."
        : undefined,
      webhookHost: safeWebhookHint(webhook),
      supabase: supabase?.ok ? { ok: true, order: supabase.order } : supabase,
    });
    return;
  }

  sendJson(res, 200, {
    ok: true,
    sheets: result.data,
    supabase: supabase?.ok ? { ok: true, order: supabase.order } : supabase,
  });
}
