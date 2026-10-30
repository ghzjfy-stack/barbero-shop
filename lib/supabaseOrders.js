/**
 * Server-only Supabase order + customer sync (checkout + Telegram status).
 */
import { getSupabaseAdmin } from "./supabaseAdmin.js";

function numOrNull(value) {
  if (value === "" || value == null) return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
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

function paymentLabel(payment) {
  return payment === "paypal" || payment === "PayPal" ? "PayPal" : "ביט";
}

function defaultStatus(payment) {
  return paymentLabel(payment) === "PayPal" ? "ממתין ל-PayPal" : "ממתין לביט";
}

/** Map checkout order snapshot → orders row. */
export function orderRowFromCheckout(order) {
  const details = order?.details || {};
  const payment = paymentLabel(order?.payment);
  const orderNumber = String(order?.number || order?.orderNumber || "").trim().toUpperCase();
  return {
    order_number: orderNumber,
    status: String(order?.status || defaultStatus(order?.payment)).trim() || defaultStatus(order?.payment),
    paid: order?.paid === "Yes" || order?.status === "שולם" ? "Yes" : "No",
    payment,
    total: numOrNull(order?.total),
    subtotal: numOrNull(order?.subtotal),
    shipping: numOrNull(order?.shipping),
    discount: numOrNull(order?.discount) || 0,
    coupon: String(order?.coupon || "").trim() || null,
    customer_name: String(details.name || order?.name || "").trim() || null,
    customer_phone: String(details.phone || order?.phone || "").trim() || null,
    customer_email: String(details.email || order?.email || "").trim().toLowerCase() || null,
    city: String(details.city || order?.city || "").trim() || null,
    address: String(details.address || order?.address || "").trim() || null,
    unit: String(details.unit || order?.unit || "").trim() || null,
    postal: String(details.postal || order?.postal || "").trim() || null,
    notes: String(details.notes || order?.notes || "").trim() || null,
    items: String(order?.items || buildItemsText(order?.lines) || "").trim() || null,
    lines: Array.isArray(order?.lines) ? order.lines : null,
    raw: order || null,
    updated_at: new Date().toISOString(),
  };
}

export async function upsertCustomerFromOrder(order) {
  const { client } = getSupabaseAdmin();
  if (!client) return { ok: false, error: "supabase_not_configured" };

  const details = order?.details || {};
  const name = String(details.name || order?.name || "").trim();
  const phone = String(details.phone || order?.phone || "").trim();
  const email = String(details.email || order?.email || "").trim().toLowerCase();
  if (name.length < 2 || phone.replace(/[^\d]/g, "").length < 9) {
    return { ok: false, error: "invalid_customer" };
  }

  const row = {
    name,
    phone,
    email: email || null,
    city: String(details.city || order?.city || "").trim() || null,
    address: String(details.address || order?.address || "").trim() || null,
    unit: String(details.unit || order?.unit || "").trim() || null,
    postal: String(details.postal || order?.postal || "").trim() || null,
    notes: String(details.notes || order?.notes || "").trim() || null,
    last_order_number: String(order?.number || order?.orderNumber || "").trim().toUpperCase() || null,
    updated_at: new Date().toISOString(),
  };

  const existing = await client.from("customers").select("id").eq("phone", phone).maybeSingle();
  if (existing.data?.id) {
    const { data, error } = await client
      .from("customers")
      .update(row)
      .eq("id", existing.data.id)
      .select("id, name, phone, email")
      .maybeSingle();
    if (error) return { ok: false, error: error.message };
    return { ok: true, customer: data };
  }

  const inserted = await client.from("customers").insert(row).select("id, name, phone, email").maybeSingle();
  if (inserted.error) return { ok: false, error: inserted.error.message };
  return { ok: true, customer: inserted.data };
}

export async function upsertOrder(order) {
  const { client } = getSupabaseAdmin();
  if (!client) return { ok: false, error: "supabase_not_configured" };

  const row = orderRowFromCheckout(order);
  if (!row.order_number) return { ok: false, error: "missing_order_number" };

  const { data, error } = await client
    .from("orders")
    .upsert(row, { onConflict: "order_number" })
    .select("id, order_number, status, paid, total, customer_name, customer_phone, customer_email")
    .single();

  if (error) return { ok: false, error: error.message };

  const customer = await upsertCustomerFromOrder(order);
  return { ok: true, order: data, customer };
}

export async function setOrderStatus(orderNumber, status, extra = {}) {
  const { client } = getSupabaseAdmin();
  if (!client) return { ok: false, error: "supabase_not_configured" };

  const number = String(orderNumber || "").trim().toUpperCase();
  if (!number) return { ok: false, error: "missing_order_number" };

  const paid =
    extra.paid ||
    (status === "שולם" ? "Yes" : status === "בוטל" ? "No" : undefined);

  const patch = {
    status: String(status || "").trim(),
    updated_at: new Date().toISOString(),
  };
  if (paid) patch.paid = paid;

  // Keep customer fields fresh when Telegram card has them.
  const mapped = orderRowFromCheckout({
    number,
    status,
    paid,
    ...extra,
    details: {
      name: extra.name,
      phone: extra.phone,
      email: extra.email,
      city: extra.city,
      address: extra.address,
      unit: extra.unit,
      postal: extra.postal,
      notes: extra.notes,
    },
  });
  for (const key of [
    "customer_name",
    "customer_phone",
    "customer_email",
    "city",
    "address",
    "unit",
    "postal",
    "notes",
    "items",
    "payment",
    "total",
  ]) {
    if (mapped[key] != null && mapped[key] !== "") patch[key] = mapped[key];
  }

  const existing = await client.from("orders").select("id").eq("order_number", number).maybeSingle();
  if (existing.data?.id) {
    const { data, error } = await client
      .from("orders")
      .update(patch)
      .eq("order_number", number)
      .select("id, order_number, status, paid")
      .single();
    if (error) return { ok: false, error: error.message };
    return { ok: true, order: data };
  }

  // Order missing in Supabase (older Sheets-only) — create from Telegram/Sheets fields.
  const created = await upsertOrder({
    number,
    status,
    paid: paid || "No",
    payment: extra.payment,
    total: extra.total,
    items: extra.items,
    details: {
      name: extra.name,
      phone: extra.phone,
      email: extra.email,
      city: extra.city,
      address: extra.address,
      unit: extra.unit,
      postal: extra.postal,
      notes: extra.notes || "נוצר מעדכון סטטוס טלגרם",
    },
  });
  return created;
}

export async function getOrderByNumber(orderNumber) {
  const { client } = getSupabaseAdmin();
  if (!client) return { ok: false, error: "supabase_not_configured" };
  const number = String(orderNumber || "").trim().toUpperCase();
  if (!number) return { ok: false, error: "missing_order_number" };
  const { data, error } = await client.from("orders").select("*").eq("order_number", number).maybeSingle();
  if (error) return { ok: false, error: error.message };
  if (!data) return { ok: false, error: "order_not_found" };
  return { ok: true, order: data };
}
