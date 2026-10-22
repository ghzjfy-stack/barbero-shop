import { useEffect } from "react";
import { StoreProvider } from "./store";
import { usePathname } from "./navigate";
import AnnouncementBar from "./components/AnnouncementBar";
import Header from "./components/Header";
import MobileMenu from "./components/MobileMenu";
import Hero from "./components/Hero";
import TrustGrid from "./components/TrustGrid";
import Catalog from "./components/Catalog";
import About from "./components/About";
import Footer from "./components/Footer";
import CartDrawer from "./components/CartDrawer";
import WishlistDrawer from "./components/WishlistDrawer";
import SearchModal from "./components/SearchModal";
import QuickView from "./components/QuickView";
import InfoDialog from "./components/InfoDialog";
import Toast from "./components/Toast";
import WhatsAppButton from "./components/WhatsAppButton";

function Shell() {
  const path = usePathname();
  const about = path === "/about";

  useEffect(() => {
    document.title = about
      ? "אודות | BARBERO"
      : "BARBERO | מכונות תספורת וגילוח ביבוא ישיר";
    if (about || !window.location.hash) {
      window.scrollTo(0, 0);
      return;
    }
    document.querySelector(window.location.hash)?.scrollIntoView();
  }, [about]);

  return (
    <>
      <a
        href="/#collection"
        className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:start-3 focus:z-[90] focus:bg-gold focus:px-4 focus:py-2 focus:text-ink"
      >
        דלגו לקולקציה
      </a>
      <div className="fixed inset-x-0 top-0 z-40 pt-[env(safe-area-inset-top,0px)]">
        <AnnouncementBar />
        <Header />
      </div>
      <main>
        {about ? (
          <About />
        ) : (
          <>
            <Hero />
            <TrustGrid />
            <Catalog />
          </>
        )}
      </main>
      <Footer />
      <MobileMenu />
      <CartDrawer />
      <WishlistDrawer />
      <SearchModal />
      <QuickView />
      <InfoDialog />
      <Toast />
      <WhatsAppButton />
    </>
  );
}

export default function App() {
  return (
    <StoreProvider>
      <Shell />
    </StoreProvider>
  );
}
