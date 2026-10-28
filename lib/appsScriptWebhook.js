/**
 * Shared Google Apps Script web-app client for Vercel serverless.
 * Avoids fetch auto-follow (which breaks Apps Script 302 → echo).
 */

import https from "node:https";
import http from "node:http";
import { URL as NodeURL } from "node:url";

/** Proven /exec with get+status (rev inplace-status). Overrides the old track-only URL. */
const LIVE_SHEETS_WEBHOOK =
  "https://script.google.com/macros/s/AKfycbw8QIHNrlMObKigJoTBqUAk-hCsIw2Uhncxy58VIuCBXXYTiz3N2nXHE4Vnmc54S3piYA/exec";
const LEGACY_SHEETS_EXEC = "AKfycbxlXCrLI4gZlOgJduULUXwLwXbVWXmDfZo5Y4T5kBi_NrcksteEruaZvGqpPAz3CQW8aA";

export function sheetsWebhookUrl() {
  const fromEnv = String(process.env.GOOGLE_SHEETS_WEBHOOK_URL || "").trim();
  if (!fromEnv || fromEnv.includes(LEGACY_SHEETS_EXEC)) return LIVE_SHEETS_WEBHOOK;
  return fromEnv;
}

export function safeWebhookHint(url) {
  try {
    const parsed = new NodeURL(url);
    const parts = parsed.pathname.split("/").filter(Boolean);
    const id = parts[parts.length - 2] || parts[parts.length - 1] || "";
    return `${parsed.host}/…/${id.slice(0, 10)}…/${parts[parts.length - 1] || ""}`;
  } catch {
    return "invalid_url";
  }
}

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

export async function postAppsScript(url, payload) {
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
