/** Fire-and-forget: append checkout order to Google Sheets via /api/sheets-order. */
export function notifySheetsOrder(order) {
  if (!order?.number) return;

  const body = {
    ...order,
    createdAt: order.createdAt || new Date().toISOString(),
  };

  void fetch("/api/sheets-order", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    keepalive: true,
  }).catch(() => {
    // Checkout must not fail if Sheets is down or env is missing.
  });
}
