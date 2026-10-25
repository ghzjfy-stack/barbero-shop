/**
 * Signed pay-page links for order confirmation emails.
 * Secret: PAY_LINK_SECRET, else RESEND_API_KEY (already on Vercel).
 */
import { createHmac, timingSafeEqual } from "crypto";

function paySecret() {
  return String(process.env.PAY_LINK_SECRET || process.env.RESEND_API_KEY || "").trim();
}

export function normalizePayment(value) {
  return value === "paypal" ? "paypal" : "bit";
}

export function normalizeAmount(value) {
  const n = Number(value);
  if (!Number.isFinite(n) || n <= 0) return null;
  return n.toFixed(2);
}

function payload({ orderNumber, total, payment }) {
  const amount = normalizeAmount(total);
  const method = normalizePayment(payment);
  const number = String(orderNumber || "").trim().toUpperCase();
  if (!number || !amount) return null;
  return `${number}|${amount}|${method}`;
}

export function signPayLink(input) {
  const secret = paySecret();
  const body = payload(input);
  if (!secret || !body) return null;
  return createHmac("sha256", secret).update(body).digest("hex");
}

export function verifyPayLink(input) {
  const expected = signPayLink(input);
  const got = String(input?.token || input?.k || "").trim().toLowerCase();
  if (!expected || !got || expected.length !== got.length) return false;
  try {
    return timingSafeEqual(Buffer.from(expected), Buffer.from(got));
  } catch {
    return false;
  }
}

export function siteOrigin() {
  const explicit = String(process.env.PUBLIC_SITE_URL || process.env.SITE_URL || "").trim();
  if (explicit) return explicit.replace(/\/$/, "");
  const prod = String(process.env.VERCEL_PROJECT_PRODUCTION_URL || "").trim();
  if (prod) return `https://${prod.replace(/^https?:\/\//, "")}`;
  const vercel = String(process.env.VERCEL_URL || "").trim();
  if (vercel) return `https://${vercel.replace(/^https?:\/\//, "")}`;
  return "https://barbero-ten.vercel.app";
}

/** Absolute /pay URL with signed query params. */
export function buildPayPageUrl({ orderNumber, total, payment }) {
  const amount = normalizeAmount(total);
  const method = normalizePayment(payment);
  const number = String(orderNumber || "").trim().toUpperCase();
  const token = signPayLink({ orderNumber: number, total: amount, payment: method });
  if (!token || !number || !amount) return null;
  const url = new URL("/pay", `${siteOrigin()}/`);
  url.searchParams.set("o", number);
  url.searchParams.set("t", amount);
  url.searchParams.set("p", method);
  url.searchParams.set("k", token);
  return url.toString();
}
