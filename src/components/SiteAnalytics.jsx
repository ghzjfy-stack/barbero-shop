import { useEffect } from "react";
import { Analytics } from "@vercel/analytics/react";
import { SpeedInsights } from "@vercel/speed-insights/react";
import { usePathname } from "../navigate";
import { ensureMetaPixel, isMetaPixelEnabled, trackMetaPageView } from "../metaPixel";

/** Public GA4 Measurement ID (safe in the browser). Set in Vercel as VITE_GA_MEASUREMENT_ID. */
const GA_ID = String(import.meta.env.VITE_GA_MEASUREMENT_ID || "").trim();

function ensureGtag(measurementId) {
  if (typeof window === "undefined" || !measurementId) return;
  if (window.gtag && window.__barberoGaId === measurementId) return;

  window.dataLayer = window.dataLayer || [];
  window.gtag = function gtag() {
    window.dataLayer.push(arguments);
  };
  window.__barberoGaId = measurementId;

  if (!document.getElementById("barbero-ga4")) {
    const script = document.createElement("script");
    script.id = "barbero-ga4";
    script.async = true;
    script.src = `https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(measurementId)}`;
    document.head.appendChild(script);
  }

  window.gtag("js", new Date());
  window.gtag("config", measurementId, {
    send_page_view: false,
    anonymize_ip: true,
  });
}

function trackGaPageView(path) {
  if (!GA_ID || typeof window === "undefined" || !window.gtag) return;
  window.gtag("event", "page_view", {
    page_path: path,
    page_location: window.location.href,
    page_title: document.title,
  });
}

/** Vercel Web Analytics + optional GA4 + Meta Pixel (SPA page views). */
export default function SiteAnalytics() {
  const path = usePathname();

  useEffect(() => {
    if (GA_ID) ensureGtag(GA_ID);
    if (isMetaPixelEnabled()) ensureMetaPixel();
  }, []);

  useEffect(() => {
    const full = path + window.location.search + window.location.hash;
    if (GA_ID) {
      ensureGtag(GA_ID);
      trackGaPageView(full);
    }
    if (isMetaPixelEnabled()) {
      ensureMetaPixel();
      trackMetaPageView();
    }
  }, [path]);

  return (
    <>
      <Analytics />
      <SpeedInsights />
    </>
  );
}
