/**
 * POST /api/send-email — send a Hebrew RTL order-confirmation email via Resend.
 *
 * Vercel / local env:
 *   RESEND_API_KEY   (required)
 *   RESEND_TO_EMAIL  (optional default recipient; body.to overrides)
 *   RESEND_FROM      (optional; default Barbero <onboarding@resend.dev>)
 *   PUBLIC_SITE_URL  (optional; absolute origin for the pay-page CTA)
 *   PAY_LINK_SECRET  (optional; defaults to RESEND_API_KEY for signed /pay links)
 */

import { Resend } from "resend";
import { buildPayPageUrl } from "../lib/payLink.js";

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

function isValidEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(value || "").trim());
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function formatIls(amount) {
  const n = Number(amount);
  if (!Number.isFinite(n)) return "";
  return `₪${n.toLocaleString("he-IL")}`;
}

function buildItemsHtml(lines = []) {
  if (!Array.isArray(lines) || lines.length === 0) return "";
  const rows = lines
    .map((line) => {
      const qty = Number(line.qty) || 1;
      const label = line.label ? ` · ${escapeHtml(line.label)}` : "";
      const total = formatIls(line.lineTotal);
      return `<tr>
        <td style="padding:8px 0;border-bottom:1px solid #2a2a2a;text-align:right;color:#f5f1e8;font-size:14px;">
          ${escapeHtml(line.name || "מוצר")}${label} × ${qty}
        </td>
        <td style="padding:8px 0;border-bottom:1px solid #2a2a2a;text-align:left;color:#cfc8bb;font-size:14px;white-space:nowrap;">
          ${escapeHtml(total)}
        </td>
      </tr>`;
    })
    .join("");
  return `<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-top:18px;">${rows}</table>`;
}

function buildPayCtaHtml(payUrl) {
  if (!payUrl) return "";
  const href = escapeHtml(payUrl);
  return `<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-top:24px;">
    <tr>
      <td align="center" style="text-align:center;">
        <a href="${href}"
           style="display:inline-block;background:#c6a15b;color:#0b0b0c;font-size:16px;font-weight:700;text-decoration:none;padding:14px 28px;border-radius:999px;letter-spacing:0.02em;">
          להשלמת התשלום
        </a>
        <div style="margin-top:12px;font-size:12px;line-height:1.6;color:#7d766b;">
          הכפתור פותח דף תשלום קצר עם האמצעי שבחרתם בהזמנה.
        </div>
      </td>
    </tr>
  </table>`;
}

function buildOrderEmailHtml({ orderNumber, customerName, total, payment, lines, payUrl }) {
  const safeOrder = escapeHtml(orderNumber);
  const safeName = escapeHtml(customerName || "לקוח/ה יקר/ה");
  const totalText = formatIls(total);
  const paymentLabel = payment === "paypal" ? "PayPal" : "ביט";
  const itemsHtml = buildItemsHtml(lines);
  const payCtaHtml = buildPayCtaHtml(payUrl);

  return `<!DOCTYPE html>
<html lang="he" dir="rtl">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>אישור הזמנה — BARBERO</title>
  </head>
  <body style="margin:0;padding:0;background:#0b0b0c;font-family:Arial,Helvetica,sans-serif;color:#f5f1e8;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#0b0b0c;padding:32px 16px;">
      <tr>
        <td align="center">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:560px;background:#141414;border:1px solid #2a2a2a;border-radius:16px;overflow:hidden;">
            <tr>
              <td style="padding:28px 28px 12px;text-align:right;background:linear-gradient(160deg,#1a1814,#0f0f10);">
                <div style="font-size:13px;letter-spacing:0.12em;color:#c6a15b;font-weight:700;">BARBERO</div>
                <h1 style="margin:10px 0 0;font-size:24px;line-height:1.35;color:#f5f1e8;font-weight:700;">
                  אישור הזמנה
                </h1>
              </td>
            </tr>
            <tr>
              <td style="padding:8px 28px 28px;text-align:right;direction:rtl;">
                <p style="margin:0 0 14px;font-size:16px;line-height:1.7;color:#f5f1e8;">
                  שלום ${safeName},
                </p>
                <p style="margin:0 0 18px;font-size:15px;line-height:1.75;color:#cfc8bb;">
                  תודה שהזמנת מ־BARBERO. קיבלנו את ההזמנה שלך והיא ממתינה להשלמת התשלום ב־${escapeHtml(paymentLabel)}.
                </p>
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#1c1a17;border:1px solid #3a342a;border-radius:12px;">
                  <tr>
                    <td style="padding:16px 18px;text-align:right;direction:rtl;">
                      <div style="font-size:12px;color:#c6a15b;margin-bottom:6px;">מספר הזמנה</div>
                      <div style="font-size:20px;font-weight:700;color:#f5f1e8;letter-spacing:0.04em;">${safeOrder}</div>
                      ${
                        totalText
                          ? `<div style="margin-top:12px;font-size:12px;color:#c6a15b;">סה״כ לתשלום</div>
                             <div style="font-size:18px;font-weight:700;color:#f5f1e8;margin-top:4px;">${escapeHtml(totalText)}</div>`
                          : ""
                      }
                    </td>
                  </tr>
                </table>
                ${itemsHtml}
                ${payCtaHtml}
                <p style="margin:20px 0 0;font-size:14px;line-height:1.7;color:#a89f90;">
                  זמן האספקה המשוער הוא 7–14 ימי עסקים. לשאלות אפשר לפנות ל־
                  <a href="mailto:support@barbero.co.il" style="color:#c6a15b;text-decoration:none;">support@barbero.co.il</a>
                  או בוואטסאפ.
                </p>
              </td>
            </tr>
            <tr>
              <td style="padding:16px 28px 24px;border-top:1px solid #2a2a2a;text-align:right;direction:rtl;">
                <div style="font-size:12px;line-height:1.6;color:#7d766b;">
                  © BARBERO — ציוד תספורת וגילוח ביבוא ישיר מארה״ב
                </div>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>`;
}

export default async function handler(req, res) {
  res.setHeader("Cache-Control", "no-store");

  if (req.method === "OPTIONS") {
    res.statusCode = 204;
    res.end();
    return;
  }

  if (req.method === "GET") {
    const configured = Boolean(String(process.env.RESEND_API_KEY || "").trim());
    sendJson(res, 200, {
      ok: true,
      service: "resend",
      configured,
      hint: "POST { to?, orderNumber?, customerName? } to send a test confirmation email",
    });
    return;
  }

  if (req.method !== "POST") {
    sendJson(res, 405, { ok: false, error: "method_not_allowed" });
    return;
  }

  const apiKey = String(process.env.RESEND_API_KEY || "").trim();
  if (!apiKey) {
    sendJson(res, 503, {
      ok: false,
      error: "resend_not_configured",
      missing: { RESEND_API_KEY: true },
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

  const to =
    String(body?.to || process.env.RESEND_TO_EMAIL || "")
      .trim()
      .toLowerCase() || "";
  if (!isValidEmail(to)) {
    sendJson(res, 400, {
      ok: false,
      error: "invalid_to_email",
      hint: "Pass body.to or set RESEND_TO_EMAIL",
    });
    return;
  }

  const orderNumber = String(body?.orderNumber || `BRB-TEST-${Date.now().toString(36).toUpperCase()}`).trim();
  const customerName = String(body?.customerName || "").trim();
  const total = body?.total;
  const payment = body?.payment === "paypal" ? "paypal" : "bit";
  const lines = Array.isArray(body?.lines) ? body.lines : [];
  const from = String(process.env.RESEND_FROM || "BARBERO <onboarding@resend.dev>").trim();
  const payUrl = buildPayPageUrl({ orderNumber, total, payment });

  try {
    const resend = new Resend(apiKey);
    const { data, error } = await resend.emails.send({
      from,
      to: [to],
      subject: `אישור הזמנה ${orderNumber} — BARBERO`,
      html: buildOrderEmailHtml({ orderNumber, customerName, total, payment, lines, payUrl }),
    });

    if (error) {
      sendJson(res, 502, {
        ok: false,
        error: "resend_send_failed",
        detail: error.message || String(error),
      });
      return;
    }

    sendJson(res, 200, {
      ok: true,
      id: data?.id ?? null,
      to,
      orderNumber,
      payUrl: payUrl || null,
    });
  } catch (error) {
    sendJson(res, 500, {
      ok: false,
      error: "resend_exception",
      detail: error?.message || String(error),
    });
  }
}
