import { useEffect, useState } from "react";
import { navLinks } from "../data";
import { useStore } from "../store";
import { IconBag, IconHeart, IconMenu, IconSearch } from "./Icons";

function CountBadge({ count }) {
  if (!count) return null;
  return (
    <span
      key={count}
      className="badge-pop absolute top-1 start-1 grid h-[1.15rem] min-w-[1.15rem] place-items-center bg-gold px-1 text-[10px] font-semibold text-[#16120b]"
    >
      {count > 99 ? "99+" : count}
    </span>
  );
}

export function Logo() {
  return (
    <a href="#top" dir="ltr" className="flex min-w-0 items-center gap-2.5 sm:gap-3">
      <span className="grid h-10 w-10 shrink-0 place-items-center border border-gold/70 font-display text-lg text-gold sm:h-11 sm:w-11 sm:text-xl">
        B
      </span>
      <span className="flex min-w-0 flex-col leading-none">
        <span className="font-display text-[1.05rem] tracking-[0.2em] text-ivory sm:text-[1.35rem] sm:tracking-[0.28em]">
          BARBERO
        </span>
        <span className="mt-1 hidden text-[10px] text-gold-soft min-[420px]:block">בית לציוד תספורת וגילוח מקצועי</span>
      </span>
    </a>
  );
}

export default function Header() {
  const {
    cartCount,
    wishCount,
    cartOpen,
    wishOpen,
    searchOpen,
    menuOpen,
    setMenuOpen,
    openCart,
    openWish,
    openSearch,
    goToCategory,
  } = useStore();
  const [solid, setSolid] = useState(false);

  useEffect(() => {
    const onScroll = () => setSolid(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={`transition-colors duration-300 ${
        solid || menuOpen
          ? "border-b border-white/10 bg-ink/92 backdrop-blur-md"
          : "border-b border-transparent bg-gradient-to-b from-ink/80 to-transparent"
      }`}
    >
      <div className="mx-auto flex h-[4.5rem] max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <div className="flex min-w-0 items-center gap-8">
          <Logo />
          <nav className="hidden items-center gap-6 md:flex" aria-label="ראשי">
            {navLinks.map((link) => (
              <a
                key={link.label}
                href={link.href}
                onClick={() => {
                  if (link.category || link.href === "#collection") goToCategory(link.category || "הכל");
                }}
                className="text-sm text-ivory/85 transition-colors hover:text-gold-soft"
              >
                {link.label}
              </a>
            ))}
          </nav>
        </div>

        <div className="flex shrink-0 items-center">
          <button type="button" className="icon-btn" aria-label="חיפוש" aria-expanded={searchOpen} onClick={openSearch}>
            <IconSearch />
          </button>
          <button type="button" className="icon-btn" aria-label="רשימת משאלות" aria-expanded={wishOpen} onClick={openWish}>
            <IconHeart />
            <CountBadge count={wishCount} />
          </button>
          <button
            type="button"
            className="icon-btn"
            aria-label="עגלת קניות"
            aria-expanded={cartOpen}
            aria-controls="cart-drawer"
            onClick={openCart}
          >
            <IconBag />
            <CountBadge count={cartCount} />
          </button>
          <button
            type="button"
            className="icon-btn desktop-hide"
            aria-label={menuOpen ? "סגירת תפריט" : "פתיחת תפריט"}
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((open) => !open)}
          >
            <IconMenu />
          </button>
        </div>
      </div>
    </header>
  );
}
