/**
 * POST /api/sheets-order — forward a checkout order to a Google Apps Script
 * web app that appends a row to the BARBERO orders Google Sheet.
 *
 * Vercel env:
 *   GOOGLE_SHEETS_WEBHOOK_URL     — Apps Script Web App URL (ends with /exec)
 *   GOOGLE_SHEETS_WEBHOOK_SECRET  — optional shared secret (must match the script)
 */

import https from "node:https";
import http from "node:http";
import { URL as NodeURL } from "node:url";

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

/** Flat row the Apps Script appends into the sheet (column order matters). */
export function buildSheetRow(order) {
  const details = order?.details || {};
  const payment = order?.payment === "paypal" ? "PayPal" : "ביט";
  const status = payment === "PayPal" ? "ממתין ל-PayPal" : "ממתין לביט";
  return {
    status,
    createdAt: formatWhen(order?.createdAt),
    orderNumber: order?.number || "",
    name: details.name || "",
    phone: details.phone || "",
    city: details.city || "",
    address: details.address || "",
    unit: details.unit || "",
    postal: details.postal || "",
    notes: details.notes || "",
    items: buildItemsText(order?.lines),
    subtotal: formatIls(order?.subtotal),
    shipping: formatIls(order?.shipping),
    total: formatIls(order?.total),
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

  const webhook = String(process.env.GOOGLE_SHEETS_WEBHOOK_URL || "").trim();

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

  let result;
  try {
    result = await postAppsScript(webhook, payload);
  } catch {
    sendJson(res, 502, { ok: false, error: "sheets_unreachable" });
    return;
  }

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
    });
    return;
  }

  sendJson(res, 200, { ok: true, sheets: result.data });
}

function safeWebhookHint(url) {
  try {
    const parsed = new NodeURL(url);
    const parts = parsed.pathname.split("/").filter(Boolean);
    const id = parts[parts.length - 2] || parts[parts.length - 1] || "";
    return `${parsed.host}/…/${id.slice(0, 10)}…/${parts[parts.length - 1] || ""}`;
  } catch {
    return "invalid_url";
  }
}

/** Node http(s) does not auto-follow redirects — required for Apps Script web apps. */
function rawRequest(url, { method = "GET", headers = {}, body } = {}) {
  return new Promise((resolve, reject) => {
    const parsed = new NodeURL(url);
    const lib = parsed.protocol === "http:" ? http : https;
    const payload = body == null ? null : Buffer.from(String(body), "utf8");
    const req = lib.request(
      {
        protocol: parsed.protocol,
        hostname: parsed.hostname,
        port: parsed.port || undefined,
        path: `${parsed.pathname}${parsed.search}`,
        method,
        headers: {
          ...headers,
          ...(payload ? { "content-length": payload.length } : {}),
        },
      },
      (res) => {
        const chunks = [];
        res.on("data", (chunk) => chunks.push(chunk));
        res.on("end", () => {
          resolve({
            statusCode: res.statusCode || 0,
            headers: res.headers,
            body: Buffer.concat(chunks).toString("utf8"),
          });
        });
      },
    );
    req.on("error", reject);
    if (payload) req.write(payload);
    req.end();
  });
}

function parseAppsScriptBody(text, status, statusText) {
  let data = {};
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    data = { raw: String(text || "").slice(0, 300) };
  }
  const html = typeof text === "string" && text.includes("<!DOCTYPE html");
  const ok = status >= 200 && status < 300 && !html && data.ok !== false;
  return { ok, status, statusText, data };
}

/**
 * Google Apps Script web apps respond with 302 → googleusercontent.com/macros/echo.
 * Vercel's fetch often follows that redirect incorrectly (POST→405 HTML).
 * POST without following redirects, then GET the Location for the JSON body.
 */
async function postAppsScript(url, payload) {
  const posted = await rawRequest(url, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      accept: "application/json,text/plain,*/*",
    },
    body: JSON.stringify(payload),
  });

  const status = posted.statusCode;
  const location = posted.headers.location;

  if (status >= 300 && status < 400) {
    if (!location) {
      return { ok: false, status, statusText: "redirect_without_location", data: {} };
    }
    const echoed = await rawRequest(location, {
      method: "GET",
      headers: { accept: "application/json,text/plain,*/*" },
    });
    return parseAppsScriptBody(echoed.body, echoed.statusCode, String(echoed.statusCode));
  }

  return parseAppsScriptBody(posted.body, status, String(status));
}
