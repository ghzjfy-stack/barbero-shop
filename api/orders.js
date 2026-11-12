/**
 * POST /api/orders — upsert full checkout order (+ customer) into Supabase.
 * GET  /api/orders — health / configuration check.
 *
 * Body: same checkout snapshot used by sheets/telegram (number, details, lines, totals…).
 * Requires SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY and supabase/schema.sql applied.
 */

import { getSupabaseAdmin } from "../lib/supabaseAdmin.js";
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
      service: "supabase-orders",
      configured: Boolean(client),
      missing: missing || undefined,
      hint: client
        ? "POST checkout order JSON to upsert into public.orders + public.customers"
        : "Set SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY, run supabase/schema.sql, Redeploy",
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
      hint: "Set SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY in Vercel, run supabase/schema.sql, Redeploy",
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

  const orderNumber = String(body?.number || body?.orderNumber || "").trim();
  if (!orderNumber) {
    sendJson(res, 400, { ok: false, error: "missing_order_number" });
    return;
  }

  const result = await upsertOrder(body);
  if (!result.ok) {
    sendJson(res, 502, {
      ok: false,
      error: "supabase_upsert_failed",
      detail: result.error,
      hint:
        result.error?.includes("Could not find the table") || result.error?.includes("schema cache")
          ? "Run supabase/schema.sql in the Supabase SQL Editor, then retry"
          : undefined,
    });
    return;
  }

  sendJson(res, 200, {
    ok: true,
    order: result.order,
    customer: result.customer?.ok === false ? { ok: false, error: result.customer.error } : result.customer,
  });
}
