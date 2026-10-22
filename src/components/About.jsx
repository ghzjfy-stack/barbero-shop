import { onNavClick } from "../navigate";

export default function About() {
  return (
    <article className="bg-ink">
      <div className="mx-auto flex min-h-[100svh] max-w-3xl flex-col justify-center px-4 pt-[calc(8rem+env(safe-area-inset-top,0px))] pb-24 sm:px-6 sm:pb-32">
        <p className="text-[11px] tracking-[0.16em] text-gold sm:text-xs sm:tracking-[0.28em]" dir="ltr">
          BARBERO
        </p>
        <h1 className="mt-4 font-display text-4xl leading-tight sm:text-6xl">אודות</h1>
        <div className="mt-8 h-px w-16 bg-gold/70" aria-hidden="true" />
        <p className="mt-8 text-lg leading-9 text-ivory/85 sm:text-xl sm:leading-10">
          BARBERO הוא בית ליבוא ישיר של ציוד תספורת וגילוח מקצועי ומקורי מארה״ב, המיועד למספרות ולשימוש ביתי ברמה הגבוהה ביותר.
        </p>
        <a href="/#collection" className="btn-gold mt-10 h-12 w-fit px-7" onClick={(event) => onNavClick(event, { href: "/#collection" })}>
          לקולקציה
        </a>
      </div>
    </article>
  );
}
