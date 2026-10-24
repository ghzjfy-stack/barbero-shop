/** Fire-and-forget order alert to /api/telegram-order (Vercel + Telegram Bot API). */
export function notifyTelegramOrder(order) {
  if (!order?.number) return;

  const body = {
    ...order,
    createdAt: order.createdAt || new Date().toISOString(),
  };

  void fetch("/api/telegram-order", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    keepalive: true,
  }).catch(() => {
    // Checkout must not fail if Telegram is down or env is missing.
  });
}
