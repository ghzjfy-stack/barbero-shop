import { useState } from "react";
import { navLinks, serviceLinks } from "../data";
import { useStore } from "../store";
import { Logo } from "./Header";

export default function Footer() {
  const { openInfo, goToCategory } = useStore();
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState("idle");
  const year = new Date().getFullYear();

  const subscribe = (event) => {
    event.preventDefault();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      setStatus("invalid");
      return;
    }
    setStatus("done");
  };

  return (
    <footer id="about" className="border-t border-white/10 bg-[#0b0b0c]">
      <div className="mx-auto grid max-w-7xl gap-12 px-4 py-16 sm:px-6 md:grid-cols-2 lg:grid-cols-4 lg:px-8">
        <div>
          <Logo />
          <p className="mt-5 max-w-xs text-sm leading-7 text-muted">
            BARBERO מביאה מכונות תספורת, גילוח וטיפוח מקוריות — למספרות, ולמי שמתייחס לבוקר כמו לטקס.
          </p>
          <div className="mt-6">
            <p className="text-sm">עדכונים על הקולקציה</p>
            {status === "done" ? (
              <p className="mt-3 text-sm leading-7 text-gold-soft" role="status">
                תודה. עדכונים על הקולקציה יישמרו לכתובת הזו במכשיר בלבד.
              </p>
            ) : (
              <form className="mt-3 flex" onSubmit={subscribe} noValidate>
                <label className="sr-only" htmlFor="newsletter-email">
                  כתובת אימייל
                </label>
                <input
                  id="newsletter-email"
                  type="email"
                  autoComplete="email"
                  placeholder="כתובת אימייל"
                  value={email}
                  onChange={(event) => {
                    setEmail(event.target.value);
                    setStatus("idle");
                  }}
                  className="field min-w-0 flex-1"
                />
                <button type="submit" className="btn-gold h-auto px-4 text-sm">
                  הרשמה
                </button>
              </form>
            )}
            {status === "invalid" && (
              <p className="mt-2 text-xs text-[#e7b2a4]">הזינו כתובת אימייל תקינה.</p>
            )}
          </div>
        </div>

        <div>
          <h2 className="font-display text-2xl">שירות לקוחות</h2>
          <ul className="mt-4 space-y-2">
            {serviceLinks.map((link) => (
              <li key={link.page}>
                <button type="button" className="text-sm text-muted hover:text-ivory" onClick={() => openInfo(link.page)}>
                  {link.label}
                </button>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h2 className="font-display text-2xl">הבית</h2>
          <ul className="mt-4 space-y-2">
            {navLinks.map((link) => (
              <li key={link.label}>
                <a
                  href={link.href}
                  className="text-sm text-muted hover:text-ivory"
                  onClick={() => {
                    if (link.category || link.href === "#collection") {
                      goToCategory(link.category || "הכל");
                    }
                  }}
                >
                  {link.label}
                </a>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h2 className="font-display text-2xl">יצירת קשר</h2>
          <ul className="mt-4 space-y-2 text-sm leading-7 text-muted">
            <li>רחוב אלנבי 48, תל אביב</li>
            <li>א׳–ה׳, 10:00–19:00</li>
            <li>
              <a className="hover:text-ivory" href="tel:+97235550198">
                03-555-0198
              </a>
            </li>
            <li>
              <a className="hover:text-ivory" href="mailto:hello@barbero.co.il">
                hello@barbero.co.il
              </a>
            </li>
          </ul>
        </div>
      </div>

      <div className="border-t border-white/10">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-5 sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
          <p className="text-xs text-muted">© {year} BARBERO. כל הזכויות שמורות.</p>
          <div className="flex flex-wrap items-center gap-3" aria-label="אמצעי תשלום">
            <span className="text-xs text-muted">תשלום בביט בלבד</span>
            <span className="grid h-8 min-w-12 place-items-center rounded-full bg-white px-3 text-sm font-semibold text-black" dir="ltr">
              bit
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
}

