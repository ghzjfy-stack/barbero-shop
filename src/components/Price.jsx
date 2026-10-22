import { discountPercent, formatPrice } from "../data";

export default function Price({ price, compareAt, from = false, size = "md" }) {
  const off = discountPercent(price, compareAt);
  const amountClass = size === "lg" ? "text-3xl" : "text-lg";

  return (
    <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
      {from && <span className="text-xs text-muted">החל מ־</span>}
      <span dir="ltr" className={`${amountClass} font-medium tabular-nums text-ivory`}>
        {formatPrice(price)}
      </span>
      {compareAt ? (
        <span dir="ltr" className="text-sm text-muted line-through tabular-nums">
          {formatPrice(compareAt)}
        </span>
      ) : null}
      {off > 0 ? (
        <span dir="ltr" className="text-xs font-medium text-gold">
          -{off}%
        </span>
      ) : null}
    </div>
  );
}
