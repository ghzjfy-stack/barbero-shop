import { useEffect, useState } from "react";
import { navLinks } from "../data";
import { onNavClick, usePathname } from "../navigate";
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
  const { setMenuOpen } = useStore();
  return (
    <a
      href="/"
      dir="ltr"
      className="flex min-w-0 items-center gap-2.5 sm:gap-3"
      onClick={(event) => onNavClick(event, { href: "/" }, { closeMenu: () => setMenuOpen(false) })}
    >
      <span className="grid h-9 w-9 shrink-0 place-items-center border border-gold/70 font-display text-base text-gold min-[360px]:h-10 min-[360px]:w-10 min-[360px]:text-lg sm:h-11 sm:w-11 sm:text-xl">
        B
      </span>
      <span className="flex min-w-0 flex-col leading-none">
        <span className="font-display text-[0.95rem] tracking-[0.08em] text-ivory min-[360px]:text-[1.05rem] min-[360px]:tracking-[0.2em] sm:text-[1.35rem] sm:tracking-[0.28em]">
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
    category,
  } = useStore();
  const [solid, setSolid] = useState(false);
  const path = usePathname();

  useEffect(() => {
    const onScroll = () => setSolid(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={`transition-colors duration-300 ${
        solid || menuOpen || path === "/about"
          ? "border-b border-white/10 bg-ink/92 backdrop-blur-md"
          : "border-b border-transparent bg-gradient-to-b from-ink/80 to-transparent"
      }`}
    >
      <div className="mx-auto flex h-[4.5rem] max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <div className="flex min-w-0 items-center gap-4 lg:gap-8">
          <Logo />
          <nav className="hidden items-center gap-3 md:flex lg:gap-6" aria-label="ראשי">
            {navLinks.map((link) => {
              const current =
                (link.href === "/about" && path === "/about") ||
                (link.category && path !== "/about" && category === link.category);
              return (
                <a
                  key={link.label}
                  href={link.href}
                  aria-current={current ? "page" : undefined}
                  onClick={(event) => onNavClick(event, link, { goToCategory })}
                  className={`text-[13px] whitespace-nowrap transition-colors hover:text-gold-soft lg:text-sm ${
                    current ? "text-gold-soft" : "text-ivory/85"
                  }`}
                >
                  {link.label}
                </a>
              );
            })}
          </nav>
        </div>

        <div className="flex shrink-0 items-center">
          <button type="button" className="icon-btn" aria-label="חיפוש" aria-expanded={searchOpen} onClick={openSearch}>
            <IconSearch />
          </button>
          <button type="button" className="icon-btn" aria-label="המועדפים שלי" aria-expanded={wishOpen} onClick={openWish}>
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
