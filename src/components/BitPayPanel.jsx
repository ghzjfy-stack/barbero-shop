import { useEffect, useState } from "react";
import { formatPrice } from "../data";
import { trackMetaAddPaymentInfo } from "../metaPixel";
import { copyBitAmount, openBitPayment } from "../payment";

/**
 * Clean personal-Bit pay screen: quiet auto-copy, minimal copy, one CTA.
 * (Bit personal links cannot prefill amount — clipboard is the only assist.)
 */
export default function BitPayPanel({ order, onPaidConfirm, paidMarked = false }) {
  const [amountCopied, setAmountCopied] = useState(false);
  const [opening, setOpening] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const ok = await copyBitAmount(order);
      if (!cancelled && ok) {
        setAmountCopied(true);
        window.setTimeout(() => {
          if (!cancelled) setAmountCopied(false);
        }, 2500);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [order?.number, order?.total]);

  const handleOpenBit = async () => {
    if (opening) return;
    setOpening(true);
    trackMetaAddPaymentInfo(order);
    try {
      await openBitPayment(order, {
        onCopied: (ok) => {
          if (ok) {
            setAmountCopied(true);
            window.setTimeout(() => setAmountCopied(false), 2500);
          }
        },
      });
    } finally {
      window.setTimeout(() => setOpening(false), 600);
    }
  };

  return (
    <div>
      <div className="text-center">
        <p className="text-xs tracking-wide text-muted">לתשלום בביט</p>
        <p className="mt-2 font-display text-5xl leading-none text-gold-soft tabular-nums" dir="ltr">
          {formatPrice(order.total)}
        </p>
        <p className="mt-2 text-xs text-muted">
          {order.shipping > 0 ? `כולל משלוח ${formatPrice(order.shipping)}` : "כולל משלוח חינם"}
        </p>
        <p className="mt-3 min-h-[1.25rem] text-[11px] text-gold-soft" aria-live="polite">
          {amountCopied ? "הסכום הועתק — הדביקו בביט" : "\u00a0"}
        </p>
      </div>

      <button
        type="button"
        className="btn-gold mt-4 inline-flex h-14 w-full items-center justify-center text-base"
        onClick={handleOpenBit}
        disabled={opening}
      >
        {opening ? "פותחים…" : "שלם עכשיו בביט"}
      </button>

      <button
        type="button"
        className={`mt-3 h-11 w-full border text-sm transition ${
          paidMarked
            ? "border-gold/50 bg-gold/10 text-gold-soft"
            : "border-white/15 text-ivory hover:border-gold/40"
        }`}
        onClick={onPaidConfirm}
        disabled={paidMarked}
      >
        {paidMarked ? "תודה — קיבלנו אישור תשלום" : "אישרתי ששילמתי"}
      </button>
    </div>
  );
}
