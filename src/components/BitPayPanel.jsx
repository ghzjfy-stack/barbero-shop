import { useEffect, useState } from "react";
import { formatPrice } from "../data";
import { trackMetaAddPaymentInfo } from "../metaPixel";
import { copyBitAmount, openBitPayment, openPayBoxPayment } from "../payment";
import { BitMark, PayBoxMark } from "./PaymentMarks";

/**
 * Clean personal Bit / PayBox pay screen: quiet auto-copy, minimal copy, one CTA.
 * (Personal links cannot prefill amount — clipboard is the only assist.)
 */
export default function BitPayPanel({ order, provider = "bit" }) {
  const isPayBox = provider === "paybox";
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
  }, [order?.number, order?.total, provider]);

  const handleOpen = async () => {
    if (opening) return;
    setOpening(true);
    trackMetaAddPaymentInfo(order);
    const open = isPayBox ? openPayBoxPayment : openBitPayment;
    try {
      await open(order, {
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

  const label = isPayBox ? "PayBox" : "ביט";
  const pasteHint = isPayBox ? "הסכום הועתק — הדביקו ב-PayBox" : "הסכום הועתק — הדביקו בביט";
  const cta = isPayBox ? "שלם עכשיו ב-PayBox" : "שלם עכשיו בביט";
  const accentBtn = isPayBox
    ? "inline-flex h-14 w-full items-center justify-center gap-2 bg-[#7B2CBF] text-base font-semibold text-white transition hover:bg-[#6920a8]"
    : "btn-gold inline-flex h-14 w-full items-center justify-center gap-2 text-base";

  return (
    <div>
      <div className="text-center">
        <p className="text-xs tracking-wide text-muted">לתשלום ב{isPayBox ? "-PayBox" : "ביט"}</p>
        <p className="mt-2 font-display text-5xl leading-none text-gold-soft tabular-nums" dir="ltr">
          {formatPrice(order.total)}
        </p>
        <p className="mt-2 text-xs text-muted">
          {order.shipping > 0 ? `כולל משלוח ${formatPrice(order.shipping)}` : "כולל משלוח חינם"}
        </p>
        <p className="mt-3 min-h-[1.25rem] text-[11px] text-gold-soft" aria-live="polite">
          {amountCopied ? pasteHint : "\u00a0"}
        </p>
      </div>

      <button type="button" className={`mt-4 ${accentBtn}`} onClick={handleOpen} disabled={opening}>
        {isPayBox ? <PayBoxMark /> : <BitMark />}
        {opening ? "פותחים…" : cta}
      </button>
      <p className="mt-2 text-center text-[11px] text-muted">
        {label} · הסכום מועתק אוטומטית להדבקה באפליקציה
      </p>
    </div>
  );
}
