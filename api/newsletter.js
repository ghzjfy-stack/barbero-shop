/**
 * POST /api/newsletter — save a collection-updates email to Google Sheets
 * (tab "ניוזלטר" via the same Apps Script webhook as orders).
 *
 * Vercel env: GOOGLE_SHEETS_WEBHOOK_URL (+ optional GOOGLE_SHEETS_WEBHOOK_SECRET)
 */

import { postAppsScript, safeWebhookHint } from "../lib/appsScriptWebhook.js";

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

function isValidEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(value || "").trim());
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

  const webhook = String(process.env.GOOGLE_SHEETS_WEBHOOK_URL || "").trim();
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

  const email = String(body?.email || "")
    .trim()
    .toLowerCase();
  if (!isValidEmail(email)) {
    sendJson(res, 400, { ok: false, error: "invalid_email" });
    return;
  }

  const secret = String(process.env.GOOGLE_SHEETS_WEBHOOK_SECRET || "").trim();
  const payload = {
    secret: secret || undefined,
    type: "newsletter",
    email,
    createdAt: formatWhen(body?.createdAt),
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
      webhookHost: safeWebhookHint(webhook),
    });
    return;
  }

  sendJson(res, 200, { ok: true, sheets: result.data });
}
