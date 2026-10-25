/** Shared Bit / PayPal checkout helpers (cart done screen + /pay page). */

export const BIT_PERSONAL_URL =
  "https://www.bitpay.co.il/app/me/E4F7DC01-399F-3467-8DB6-0EC0B9DF1ACDF11F";

const PAYPAL_EMAIL = "ghzjfyy@gmail.com";

export function paypalPayParams(order) {
  return new URLSearchParams({
    cmd: "_xclick",
    business: PAYPAL_EMAIL,
    item_name: `BARBERO הזמנה ${order.number}`,
    amount: Number(order.total).toFixed(2),
    currency_code: "ILS",
    no_shipping: "1",
    no_note: "1",
    charset: "utf-8",
  });
}

export function paypalPayUrl(order) {
  return `https://www.paypal.com/cgi-bin/webscr?${paypalPayParams(order).toString()}`;
}

/**
 * Phone: prefer the PayPal app when installed, else the mobile web checkout.
 * Desktop: open the PayPal website in a new tab.
 */
export function openPayPalPayment(order) {
  const webUrl = paypalPayUrl(order);
  const ua = navigator.userAgent || "";
  const android = /Android/i.test(ua);
  const ios = /iPhone|iPad|iPod/i.test(ua);

  if (!android && !ios) {
    window.open(webUrl, "_blank", "noopener,noreferrer");
    return;
  }

  if (android) {
    const intent =
      `intent://www.paypal.com/cgi-bin/webscr?${paypalPayParams(order).toString()}` +
      `#Intent;scheme=https;package=com.paypal.android.p2pmobile;` +
      `S.browser_fallback_url=${encodeURIComponent(webUrl)};end`;
    window.location.href = intent;
    return;
  }

  window.location.assign(webUrl);
}
