import { SUPPORT_WHATSAPP } from "../payment";

/** Prefilled WhatsApp note — goes to BARBERO only; nothing posts to the site automatically. */
export function feedbackWhatsAppHref(productName = "") {
  const product = String(productName || "").trim();
  const lines = [
    "שלום BARBERO,",
    "קניתי אצלכם ורוצה לשתף חוויה:",
    product ? `מוצר: ${product}` : "מוצר:",
    "מה אהבתי:",
    "מה אפשר לשפר:",
    "שם:",
  ];
  return `https://wa.me/${SUPPORT_WHATSAPP}?text=${encodeURIComponent(lines.join("\n"))}`;
}

/**
 * Quiet trust invite: customers write to you on WhatsApp.
 * You choose later what (if anything) becomes a public review.
 */
export default function FeedbackInvite() {
  return (
    <section id="feedback" className="border-t border-white/10 bg-[#0b0b0c]">
      <div className="mx-auto flex max-w-7xl flex-col gap-6 px-4 py-16 sm:flex-row sm:items-end sm:justify-between sm:px-6 sm:py-20 lg:px-8">
        <div className="max-w-xl">
          <p className="mb-3 text-xs tracking-wide text-gold">חוות דעת אמיתיות</p>
          <h2 className="font-display text-3xl leading-tight sm:text-4xl">קניתם אצלנו? כתבו לנו איך היה</h2>
          <p className="mt-4 text-sm leading-7 text-muted">
            נשמח לשמוע — לטובה או לשיפור. ההודעה מגיעה אלינו ישירות בוואטסאפ.
          </p>
        </div>
        <a
          href={feedbackWhatsAppHref()}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-gold inline-flex h-12 shrink-0 items-center justify-center px-7 text-[15px]"
        >
          כתבו לנו חוויה
        </a>
      </div>
    </section>
  );
}
