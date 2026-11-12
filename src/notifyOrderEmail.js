/** Fire-and-forget: send Hebrew order-confirmation email via /api/send-email. */
export function notifyOrderEmail(order) {
  const to = String(order?.details?.email || "")
    .trim()
    .toLowerCase();
  if (!to || !order?.number) return;

  const body = {
    to,
    orderNumber: order.number,
    customerName: String(order?.details?.name || "").trim(),
    total: order.total,
    subtotal: order.subtotal,
    shipping: order.shipping,
    discount: order.discount || 0,
    coupon: order.coupon || "",
    payment: order.payment,
    lines: Array.isArray(order.lines)
      ? order.lines.map((line) => ({
          name: line.name,
          qty: line.qty,
          lineTotal: line.lineTotal,
          label: line.label,
        }))
      : [],
  };

  void fetch("/api/send-email", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    keepalive: true,
  }).catch(() => {
    // Checkout must not fail if Resend is down or env is missing.
  });
}
