import { navLinks } from "../data";
import { useStore } from "../store";
import { IconClose } from "./Icons";
import { Logo } from "./Header";

export default function MobileMenu() {
  const { menuOpen, setMenuOpen, goToCategory, openSearch, openInfo } = useStore();

  return (
    <div className={`fixed inset-0 z-50 md:hidden ${menuOpen ? "" : "pointer-events-none"}`} aria-hidden={!menuOpen}>
      <button
        type="button"
        className={`absolute inset-0 bg-black/70 transition-opacity ${menuOpen ? "opacity-100" : "opacity-0"}`}
        aria-label="סגירת תפריט"
        onClick={() => setMenuOpen(false)}
      />
      <div
        inert={menuOpen ? undefined : true}
        className={`absolute inset-y-0 right-0 flex w-[min(100%,22rem)] flex-col border-s border-white/10 bg-ink px-6 py-5 transition-transform duration-500 ${
          menuOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between">
          <Logo />
          <button type="button" className="icon-btn" aria-label="סגירה" onClick={() => setMenuOpen(false)}>
            <IconClose />
          </button>
        </div>
        <nav className="mt-10 flex flex-col" aria-label="נייד">
          {navLinks.map((link) => (
            <a
              key={link.label}
              href={link.href}
              onClick={() => {
                if (link.category || link.href === "#collection") goToCategory(link.category || "הכל");
                else setMenuOpen(false);
              }}
              className="border-b border-white/10 py-4 font-display text-4xl"
            >
              {link.label}
            </a>
          ))}
        </nav>
        <div className="mt-auto flex flex-col gap-3 pb-4">
          <button type="button" className="btn-ghost h-12" onClick={openSearch}>
            חיפוש בקולקציה
          </button>
          <button type="button" className="btn-text h-11 text-sm" onClick={() => openInfo("shipping")}>
            משלוחים ואחריות
          </button>
        </div>
      </div>
    </div>
  );
}
