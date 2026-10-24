/**
 * POST /api/sheets-order — forward a checkout order to a Google Apps Script
 * web app that appends a row to the BARBERO orders Google Sheet.
 *
 * Vercel env:
 *   GOOGLE_SHEETS_WEBHOOK_URL     — Apps Script Web App URL (ends with /exec)
 *   GOOGLE_SHEETS_WEBHOOK_SECRET  — optional shared secret (must match the script)
 */

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
  return {
    status: "ממתין לביט",
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
    payment: "ביט",
  };
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
    sendJson(res, 502, {
      ok: false,
      error: "sheets_rejected",
      detail: result.data?.error || result.data?.raw || result.statusText,
    });
    return;
  }

  sendJson(res, 200, { ok: true, sheets: result.data });
}

/**
 * Google Apps Script web apps respond with 302 → googleusercontent.com/macros/echo.
 * Some runtimes (incl. Vercel) mishandle following that redirect on POST and get HTML 405.
 * POST with redirect:manual, then GET the Location for the JSON body.
 */
async function postAppsScript(url, payload) {
  const posted = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    redirect: "manual",
  });

  let text = "";
  let status = posted.status;
  let statusText = posted.statusText;

  if (status >= 300 && status < 400) {
    const location = posted.headers.get("location");
    if (!location) {
      return { ok: false, status, statusText: "redirect_without_location", data: {} };
    }
    const echoed = await fetch(location, { method: "GET", redirect: "follow" });
    status = echoed.status;
    statusText = echoed.statusText;
    text = await echoed.text().catch(() => "");
  } else {
    text = await posted.text().catch(() => "");
  }

  let data = {};
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    data = { raw: text.slice(0, 300) };
  }

  return { ok: status >= 200 && status < 300, status, statusText, data };
}
