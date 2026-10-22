import { trustItems } from "../data";
import { TrustIcon } from "./Icons";

export default function TrustGrid() {
  return (
    <section id="trust" className="border-y border-white/10 bg-slate">
      <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 sm:py-24 lg:px-8">
        <div className="mb-10 max-w-2xl">
          <p className="mb-3 text-xs text-gold">הסטנדרט</p>
          <h2 className="font-display text-4xl leading-tight sm:text-5xl">כל דגם מגיע עם שקט</h2>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {trustItems.map((item, index) => (
            <article
              key={item.title}
              className="border border-white/10 bg-ink/50 p-6 transition duration-300 hover:-translate-y-1 hover:border-gold/45"
            >
              <div className="flex items-center justify-between">
                <span className="grid h-12 w-12 place-items-center border border-gold/35 text-gold">
                  <TrustIcon name={item.icon} />
                </span>
                <span className="font-display text-sm text-gold/70">0{index + 1}</span>
              </div>
              <h3 className="mt-6 font-display text-[1.7rem] leading-snug">{item.title}</h3>
              <p className="mt-3 text-sm leading-7 text-muted">{item.text}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
