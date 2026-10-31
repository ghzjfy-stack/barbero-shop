import { useState } from "react";
import { FIRST_ORDER_COUPON } from "../data";
import { useStore } from "../store";

/** ASOS-style promo strip: opening offer + dashed code chip (apply + copy on tap). */
export default function AnnouncementBar() {
  const store = useStore();
  const [copied, setCopied] = useState(false);

  const claimCode = async () => {
    if (store.firstOrderEligible) {
      store.applyCoupon(FIRST_ORDER_COUPON.code, { quiet: true });
    }
    try {
      await navigator.clipboard.writeText(FIRST_ORDER_COUPON.code);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      setCopied(false);
    }
  };

  return (
    <div className="border-b border-gold/35 bg-[#120f0c] text-[12px] text-gold-soft sm:text-[13px]">
      <div className="mx-auto flex min-h-9 max-w-7xl flex-wrap items-center justify-center gap-x-2.5 gap-y-1 px-3 py-1.5 text-center">
        <span className="font-medium tracking-wide text-ivory">{FIRST_ORDER_COUPON.label}</span>
        <span className="hidden text-gold/35 sm:inline" aria-hidden="true">
          |
        </span>
        <span className="flex items-center gap-1.5">
          <span className="text-muted">קוד</span>
          <button
            type="button"
            onClick={claimCode}
            className="inline-flex items-center border border-dashed border-gold/55 bg-ink/40 px-2 py-0.5 font-semibold tracking-[0.14em] text-gold transition-colors hover:border-gold hover:bg-gold/10"
            aria-label={`החלת והעתקת קוד קופון ${FIRST_ORDER_COUPON.code}`}
            dir="ltr"
          >
            {FIRST_ORDER_COUPON.code}
          </button>
          <span className={`text-[11px] ${copied ? "text-gold" : "text-muted"}`} aria-live="polite">
            {copied ? "הוחל" : store.appliedCoupon ? "פעיל בעגלה" : "לחצו להחלה"}
          </span>
        </span>
      </div>
    </div>
  );
}
