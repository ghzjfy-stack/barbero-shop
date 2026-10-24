/**
 * POST /api/customers — insert a row into public.customers.
 *
 * Body: { "name": "...", "phone": "..." }
 *
 * Current Supabase columns: id, created_at, Name (text), Email (text), Text (time).
 * Phone number is stored in Email until a text "Phone" column exists.
 */

import { getSupabaseAdmin } from "../lib/supabaseAdmin.js";

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

function normalizePhone(phone) {
  return String(phone || "").trim();
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

  const { client, missing } = getSupabaseAdmin();
  if (!client) {
    sendJson(res, 503, {
      ok: false,
      error: "supabase_not_configured",
      missing,
      hint: "Set SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY in Vercel env, then Redeploy",
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

  const name = String(body?.name || "").trim();
  const phone = normalizePhone(body?.phone);

  if (name.length < 2) {
    sendJson(res, 400, { ok: false, error: "invalid_name" });
    return;
  }
  const digits = phone.replace(/[^\d]/g, "");
  if (digits.length < 9 || digits.length > 13) {
    sendJson(res, 400, { ok: false, error: "invalid_phone" });
    return;
  }

  // Prefer a text "Phone" column when it exists; otherwise use Email (text).
  let result = await client
    .from("customers")
    .insert({ Name: name, Phone: phone })
    .select("id, created_at, Name, Phone, Email")
    .single();

  if (result.error && /Phone|schema cache/i.test(result.error.message || "")) {
    result = await client
      .from("customers")
      .insert({ Name: name, Email: phone })
      .select("id, created_at, Name, Email")
      .single();
  }

  const { data, error } = result;

  if (error) {
    sendJson(res, 502, {
      ok: false,
      error: "supabase_insert_failed",
      detail: error.message,
    });
    return;
  }

  sendJson(res, 200, {
    ok: true,
    customer: {
      id: data.id,
      created_at: data.created_at,
      name: data.Name,
      phone: data.Phone ?? data.Email ?? null,
      email: data.Phone ? data.Email ?? null : null,
    },
  });
}
