/** Shared Bit / PayPal checkout helpers (cart done screen + /pay page). */

export const BIT_PERSONAL_URL =
  "https://www.bitpay.co.il/app/me/E4F7DC01-399F-3467-8DB6-0EC0B9DF1ACDF11F";

export const SUPPORT_WHATSAPP = "972543554888";

const PAYPAL_EMAIL = "ghzjfyy@gmail.com";

/** Plain number for Bit amount field (e.g. "350" or "350.5"). */
export function bitAmountString(order) {
  const n = Number(order?.total);
  if (!Number.isFinite(n) || n < 0) return "0";
  return Number.isInteger(n) ? String(n) : n.toFixed(2);
}

export async function copyText(value) {
  const text = String(value ?? "");
  if (!text) return false;
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    try {
      const el = document.createElement("textarea");
      el.value = text;
      el.setAttribute("readonly", "");
      el.style.position = "fixed";
      el.style.opacity = "0";
      document.body.appendChild(el);
      el.select();
      const ok = document.execCommand("copy");
      document.body.removeChild(el);
      return ok;
    } catch {
      return false;
    }
  }
}

export async function copyBitAmount(order) {
  return copyText(bitAmountString(order));
}

/**
 * Friendliest personal-Bit flow we can do without a business account:
 * copy amount to clipboard, then open the personal Bit link.
 * Customer pastes into the amount field in Bit.
 */
export async function openBitPayment(order, { onCopied } = {}) {
  const ok = await copyBitAmount(order);
  if (typeof onCopied === "function") onCopied(ok);
  // Small delay so mobile browsers finish clipboard write before leaving the tab.
  await new Promise((r) => setTimeout(r, ok ? 180 : 0));
  window.open(BIT_PERSONAL_URL, "_blank", "noopener,noreferrer");
  return ok;
}

export function bitHelpWhatsAppUrl(order) {
  const amount = bitAmountString(order);
  const number = order?.number || "";
  const text = [
    `שלום BARBERO, צריך עזרה בתשלום בביט.`,
    number ? `הזמנה: ${number}` : null,
    `סכום: ₪${amount}`,
  ]
    .filter(Boolean)
    .join("\n");
  return `https://wa.me/${SUPPORT_WHATSAPP}?text=${encodeURIComponent(text)}`;
}

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
