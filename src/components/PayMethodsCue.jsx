import { BitMark, PayBoxMark } from "./PaymentMarks";

function PayPalPill() {
  return (
    <span
      className="grid h-5 place-items-center rounded-full bg-[#0070ba] px-2 text-[10px] font-semibold text-white"
      dir="ltr"
      aria-hidden="true"
    >
      PayPal
    </span>
  );
}

/**
 * Early, quiet payment reassurance — visible before final checkout
 * so shoppers know Bit / PayBox / PayPal are available.
 */
export default function PayMethodsCue({ className = "", compact = false }) {
  return (
    <div
      className={`flex flex-wrap items-center gap-x-2 gap-y-1.5 ${className}`}
      aria-label="אמצעי תשלום: ביט, PayBox ו-PayPal"
    >
      <span className="flex items-center gap-1.5" aria-hidden="true">
        <BitMark />
        <PayBoxMark />
        <PayPalPill />
      </span>
      <span className={`text-muted ${compact ? "text-[10px] leading-4" : "text-[11px] leading-4"}`}>
        {compact ? "תשלום בביט, PayBox או PayPal" : "תשלום מהיר ומאובטח בביט, PayBox או PayPal"}
      </span>
    </div>
  );
}
