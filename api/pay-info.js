/**
 * GET /api/pay-info?o=&t=&p=&k=
 * Verifies a signed pay-page link and returns order payment summary.
 */

import { normalizeAmount, normalizePayment, verifyPayLink } from "../lib/payLink.js";

function sendJson(res, status, body) {
  res.statusCode = status;
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  res.setHeader("Cache-Control", "no-store");
  res.end(JSON.stringify(body));
}

export default async function handler(req, res) {
  if (req.method === "OPTIONS") {
    res.statusCode = 204;
    res.end();
    return;
  }

  if (req.method !== "GET") {
    sendJson(res, 405, { ok: false, error: "method_not_allowed" });
    return;
  }

  const url = new URL(req.url || "/", "http://localhost");
  const orderNumber = String(url.searchParams.get("o") || "").trim().toUpperCase();
  const total = normalizeAmount(url.searchParams.get("t"));
  const payment = normalizePayment(url.searchParams.get("p"));
  const token = String(url.searchParams.get("k") || "").trim();

  if (!orderNumber || !total || !token) {
    sendJson(res, 400, { ok: false, error: "missing_params" });
    return;
  }

  if (!verifyPayLink({ orderNumber, total, payment, token })) {
    sendJson(res, 403, { ok: false, error: "invalid_or_expired_link" });
    return;
  }

  sendJson(res, 200, {
    ok: true,
    order: {
      number: orderNumber,
      total: Number(total),
      payment,
    },
  });
}
