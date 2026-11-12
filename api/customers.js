/**
 * POST /api/customers — upsert customer details into public.customers.
 * GET  /api/customers — health check.
 *
 * Prefers full checkout details (name, phone, email, address…).
 * Also used as a lightweight fallback from older clients (name + phone only).
 */

import { getSupabaseAdmin } from "../lib/supabaseAdmin.js";
import { upsertCustomerFromOrder } from "../lib/supabaseOrders.js";

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

export default async function handler(req, res) {
  res.setHeader("Cache-Control", "no-store");

  if (req.method === "OPTIONS") {
    res.statusCode = 204;
    res.end();
    return;
  }

  const { client, missing } = getSupabaseAdmin();

  if (req.method === "GET") {
    sendJson(res, 200, {
      ok: true,
      service: "supabase-customers",
      configured: Boolean(client),
      missing: missing || undefined,
    });
    return;
  }

  if (req.method !== "POST") {
    sendJson(res, 405, { ok: false, error: "method_not_allowed" });
    return;
  }

  if (!client) {
    sendJson(res, 503, {
      ok: false,
      error: "supabase_not_configured",
      missing,
      hint: "Set SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY in Vercel → Production, then Redeploy",
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

  const name = String(body?.name || body?.details?.name || "").trim();
  const phone = String(body?.phone || body?.details?.phone || "").trim();
  if (name.length < 2) {
    sendJson(res, 400, { ok: false, error: "invalid_name" });
    return;
  }
  const digits = phone.replace(/[^\d]/g, "");
  if (digits.length < 9 || digits.length > 13) {
    sendJson(res, 400, { ok: false, error: "invalid_phone" });
    return;
  }

  const result = await upsertCustomerFromOrder({
    number: body?.last_order_number || body?.orderNumber || body?.number || "",
    details: {
      name,
      phone,
      email: body?.email || body?.details?.email || "",
      city: body?.city || body?.details?.city || "",
      address: body?.address || body?.details?.address || "",
      unit: body?.unit || body?.details?.unit || "",
      postal: body?.postal || body?.details?.postal || "",
      notes: body?.notes || body?.details?.notes || "",
    },
  });

  if (!result.ok) {
    sendJson(res, 502, {
      ok: false,
      error: "supabase_upsert_failed",
      detail: result.error,
      hint: "Run supabase/schema.sql in Supabase SQL Editor (fixes legacy Phone/Email columns).",
    });
    return;
  }

  sendJson(res, 200, { ok: true, customer: result.customer });
}
