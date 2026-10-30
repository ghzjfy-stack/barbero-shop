/**
 * Save full customer details via /api/customers → Supabase `customers`.
 * Fire-and-forget — checkout must not block on Supabase.
 */
export function saveCustomer(payload = {}) {
  const body = {
    name: String(payload.name || "").trim(),
    phone: String(payload.phone || "").trim(),
    email: String(payload.email || "").trim().toLowerCase(),
    city: String(payload.city || "").trim(),
    address: String(payload.address || "").trim(),
    unit: String(payload.unit || "").trim(),
    postal: String(payload.postal || "").trim(),
    notes: String(payload.notes || "").trim(),
    last_order_number: String(payload.last_order_number || payload.orderNumber || "").trim(),
  };
  if (body.name.length < 2 || body.phone.replace(/[^\d]/g, "").length < 9) {
    return;
  }

  void fetch("/api/customers", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    keepalive: true,
  }).catch(() => {
    // Network / env failures should not break checkout.
  });
}
