/** Fire-and-forget: upsert full order + customer into Supabase via /api/orders. */
export function notifySupabaseOrder(order) {
  if (!order?.number) return;

  const body = {
    ...order,
    createdAt: order.createdAt || new Date().toISOString(),
  };

  void fetch("/api/orders", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    keepalive: true,
  }).catch(() => {
    // Checkout must not fail if Supabase is down or schema is missing.
  });
}
