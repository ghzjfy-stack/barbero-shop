import { productFaqItems } from "../data";
import { IconChevron } from "./Icons";

/** Native accordion near buy actions — short answers that unblock checkout. */
export default function ProductFaq({ className = "" }) {
  return (
    <section className={className} aria-label="שאלות נפוצות על המוצר">
      <h3 className="text-xs tracking-wide text-gold">שאלות נפוצות</h3>
      <div className="mt-3 divide-y divide-white/10 border-y border-white/10">
        {productFaqItems.map((item) => (
          <details key={item.q} className="group py-3">
            <summary className="flex cursor-pointer list-none items-center justify-between gap-3 text-start text-sm text-ivory [&::-webkit-details-marker]:hidden">
              <span>{item.q}</span>
              <IconChevron className="h-3.5 w-3.5 shrink-0 rotate-90 text-muted transition group-open:-rotate-90" />
            </summary>
            <p className="mt-2 pe-6 text-sm leading-7 text-muted">{item.a}</p>
          </details>
        ))}
      </div>
    </section>
  );
}
