/** Compact brand marks for checkout payment options. */

export function BitMark() {
  return (
    <span
      className="grid h-5 min-w-8 place-items-center rounded-full bg-white px-1.5 text-[10px] font-semibold text-black"
      dir="ltr"
    >
      bit
    </span>
  );
}

export function PayPalMark({ className = "h-4 w-auto" }) {
  return (
    <svg viewBox="0 0 80 24" className={className} aria-hidden="true">
      <text
        x="0"
        y="17"
        fill="currentColor"
        fontFamily="Helvetica, Arial, sans-serif"
        fontWeight="700"
        fontSize="16"
        letterSpacing="-0.4"
      >
        PayPal
      </text>
    </svg>
  );
}

/** PayBox wordmark — purple pill matching their brand feel. */
export function PayBoxMark({ className = "" }) {
  return (
    <span
      className={`inline-flex h-5 items-center rounded-full bg-[#7B2CBF] px-2 text-[10px] font-bold tracking-wide text-white ${className}`}
      dir="ltr"
      aria-hidden="true"
    >
      PayBox
    </span>
  );
}
