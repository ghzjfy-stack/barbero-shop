import { purchaseTrustLines } from "../data";

/** Compact reassurance under price / next to checkout — keeps the existing look. */
export default function PurchaseTrust({ className = "" }) {
  return (
    <ul className={`space-y-1 text-[11px] leading-5 text-ivory/65 ${className}`}>
      {purchaseTrustLines.map((line) => (
        <li key={line} className="flex gap-2">
          <span className="mt-[0.35em] h-1 w-1 shrink-0 rounded-full bg-gold/80" aria-hidden="true" />
          <span>{line}</span>
        </li>
      ))}
    </ul>
  );
}
