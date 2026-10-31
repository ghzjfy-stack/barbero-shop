import { useEffect, useState } from "react";
import { formatPrice } from "../data";
import { trackMetaAddPaymentInfo } from "../metaPixel";
import {
  bitAmountString,
  bitHelpWhatsAppUrl,
  copyBitAmount,
  copyText,
  openBitPayment,
} from "../payment";

/**
 * Personal Bit checkout (no business account): make the manual amount
 * as hard to mess up as possible — auto-copy, big paste hint, 3 clear steps.
 */
export default function BitPayPanel({ order, onPaidConfirm, paidMarked = false }) {
  const [amountCopied, setAmountCopied] = useState(false);
  const [numberCopied, setNumberCopied] = useState(false);
  const [opening, setOpening] = useState(false);
  const amountPlain = bitAmountString(order);

  // Prefill clipboard as soon as the pay screen appears.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      const ok = await copyBitAmount(order);
      if (!cancelled && ok) {
        setAmountCopied(true);
        window.setTimeout(() => {
          if (!cancelled) setAmountCopied(false);
        }, 4000);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [order?.number, order?.total]);

  const flashAmount = () => {
    setAmountCopied(true);
    window.setTimeout(() => setAmountCopied(false), 3500);
  };

  const handleCopyAmount = async () => {
    const ok = await copyBitAmount(order);
    if (ok) flashAmount();
  };

  const handleCopyNumber = async () => {
    const ok = await copyText(order.number);
    if (ok) {
      setNumberCopied(true);
      window.setTimeout(() => setNumberCopied(false), 2000);
    }
  };

  const handleOpenBit = async () => {
    if (opening) return;
    setOpening(true);
    trackMetaAddPaymentInfo(order);
    try {
      const ok = await openBitPayment(order, {
        onCopied: (copied) => {
          if (copied) flashAmount();
        },
      });
      if (!ok) flashAmount();
    } finally {
      window.setTimeout(() => setOpening(false), 800);
    }
  };

  return (
    <div>
      <div className="border border-gold/35 bg-gold/5 px-4 py-5 text-center">
        <p className="text-xs tracking-wide text-muted">סכום להעברה בביט</p>
        <p className="mt-2 font-display text-5xl leading-none text-gold-soft tabular-nums" dir="ltr">
          {formatPrice(order.total)}
        </p>
        <p className="mt-2 text-xs text-muted">
          {order.shipping > 0 ? `כולל משלוח ${formatPrice(order.shipping)}` : "כולל משלוח חינם"}
        </p>
        <button
          type="button"
          className={`mt-4 inline-flex h-11 min-w-[12rem] items-center justify-center border px-4 text-sm font-semibold transition ${
            amountCopied
              ? "border-gold bg-gold text-[#16120b]"
              : "border-gold/60 text-gold-soft hover:border-gold hover:bg-gold/10"
          }`}
          onClick={handleCopyAmount}
          dir="ltr"
        >
          {amountCopied ? "✓ הסכום הועתק — הדביקו בביט" : `העתיקו ${amountPlain}`}
        </button>
        <p className="mt-2 text-[11px] text-muted" aria-live="polite">
          {amountCopied
            ? "הסכום בלוח — בביט לחצו על שדה הסכום → הדבקה"
            : "לחיצה מעתיקה רק את המספר (בלי ₪)"}
        </p>
      </div>

      <ol className="mt-5 space-y-2.5 text-start text-[12px] leading-5 text-ivory/80">
        <li className="flex gap-2.5">
          <span className="grid h-5 w-5 shrink-0 place-items-center rounded-full bg-gold/20 text-[11px] font-semibold text-gold-soft">
            1
          </span>
          <span>
            לחצו «פתחו ביט» — הסכום <strong className="text-ivory tabular-nums" dir="ltr">{amountPlain}</strong>{" "}
            מועתק אוטומטית
          </span>
        </li>
        <li className="flex gap-2.5">
          <span className="grid h-5 w-5 shrink-0 place-items-center rounded-full bg-gold/20 text-[11px] font-semibold text-gold-soft">
            2
          </span>
          <span>בביט: בשדה הסכום לחצו לחיצה ארוכה → <strong className="text-ivory">הדבקה</strong></span>
        </li>
        <li className="flex gap-2.5">
          <span className="grid h-5 w-5 shrink-0 place-items-center rounded-full bg-gold/20 text-[11px] font-semibold text-gold-soft">
            3
          </span>
          <span>
            בהערה כתבו את מספר ההזמנה{" "}
            <button
              type="button"
              className="font-semibold text-gold-soft underline-offset-2 hover:underline"
              dir="ltr"
              onClick={handleCopyNumber}
            >
              {numberCopied ? "הועתק" : order.number}
            </button>
          </span>
        </li>
      </ol>

      <button
        type="button"
        className="btn-gold mt-6 inline-flex h-14 w-full items-center justify-center text-base"
        onClick={handleOpenBit}
        disabled={opening}
      >
        {opening ? "פותחים ביט…" : amountCopied ? "פתחו ביט (הסכום כבר הועתק)" : "העתיקו סכום ופתחו ביט"}
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

      <p className="mt-4 text-center text-[11px] leading-5 text-muted">
        תקועים?{" "}
        <a className="text-gold-soft hover:underline" href={bitHelpWhatsAppUrl(order)} target="_blank" rel="noopener noreferrer">
          וואטסאפ עם פרטי ההזמנה
        </a>
      </p>
    </div>
  );
}
