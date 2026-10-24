/**
 * Save a customer (name + phone) via /api/customers → Supabase `customers`.
 * Fire-and-forget friendly — checkout must not block on Supabase.
 */
export function saveCustomer({ name, phone }) {
  const payload = {
    name: String(name || "").trim(),
    phone: String(phone || "").trim(),
  };
  if (payload.name.length < 2 || payload.phone.replace(/[^\d]/g, "").length < 9) {
    return;
  }

  void fetch("/api/customers", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    keepalive: true,
  }).catch(() => {
    // Network / env failures should not break checkout.
  });
}
