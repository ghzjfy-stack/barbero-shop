import { useState } from "react";
import { navLinks, serviceLinks } from "../data";
import { onNavClick } from "../navigate";
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
    <footer className="border-t border-white/10 bg-[#0b0b0c]">
      <div className="mx-auto grid max-w-7xl gap-12 px-4 py-16 sm:px-6 md:grid-cols-2 lg:grid-cols-4 lg:px-8">
        <div>
          <Logo />
          <p className="mt-5 max-w-xs text-sm leading-7 text-muted">
            BARBERO מביאה אליכם מכונות תספורת, גילוח וטיפוח מקוריות – ביבוא ישיר מארה״ב, למספרות ולשימוש ביתי מקצועי.
          </p>
          <div className="mt-6">
            <p className="text-sm">עדכונים על הקולקציה</p>
            {status === "done" ? (
              <p className="mt-3 text-sm leading-7 text-gold-soft" role="status">
                תודה שנרשמת! נעדכן אותך ראשון על דגמים חדשים ומבצעים בלעדיים.
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
          <h2 className="font-display text-2xl">ניווט מהיר</h2>
          <ul className="mt-4 space-y-2">
            {navLinks.map((link) => (
              <li key={link.label}>
                <a
                  href={link.href}
                  className="text-sm text-muted hover:text-ivory"
                  onClick={(event) => onNavClick(event, link, { goToCategory })}
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
            <li>שעות מענה: א׳–ה׳, 09:00–18:00</li>
            <li>
              <a
                className="hover:text-ivory"
                href="https://wa.me/972543554888?text=%D7%A9%D7%9C%D7%95%D7%9D%20BARBERO%2C%20%D7%90%D7%A9%D7%9E%D7%97%20%D7%9C%D7%A7%D7%91%D7%9C%20%D7%9E%D7%99%D7%93%D7%A2%20%D7%99%D7%99%D7%A2%D7%95%D7%A5%20%D7%9C%D7%92%D7%91%D7%99%20%D7%94%D7%9E%D7%95%D7%A6%D7%A8%D7%99%D7%9D"
                target="_blank"
                rel="noopener noreferrer"
              >
                מענה בוואטסאפ בלבד
              </a>
            </li>
            <li>
              <a className="hover:text-ivory" href="mailto:support@barbero.co.il">
                support@barbero.co.il
              </a>
            </li>
          </ul>
        </div>
      </div>

      <div className="border-t border-white/10">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 pt-5 pb-[max(5.75rem,calc(5rem+env(safe-area-inset-bottom,0px)))] sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
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

