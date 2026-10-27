import { useEffect } from "react";
import { findProduct } from "./data";
import { StoreProvider } from "./store";
import { usePathname } from "./navigate";
import { parseProductFromLocation } from "./share";
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
import PayPage from "./components/PayPage";
import SiteAnalytics from "./components/SiteAnalytics";

function Shell() {
  const path = usePathname();
  const about = path === "/about";
  const pay = path === "/pay";
  const productLanding = /^\/p\//.test(path);

  useEffect(() => {
    const landedProduct = productLanding ? findProduct(parseProductFromLocation()) : null;
    document.title = pay
      ? "תשלום הזמנה | BARBERO"
      : about
        ? "אודות | BARBERO"
        : landedProduct
          ? `${landedProduct.name} | BARBERO`
          : "BARBERO | מכונות תספורת וגילוח ביבוא ישיר";
    if (pay) {
      window.scrollTo(0, 0);
      return;
    }
    // Ad / share deep-link: product modal opens on top — homepage underneath unchanged
    if ((productLanding || new URLSearchParams(window.location.search).get("product")) && !about) {
      window.scrollTo(0, 0);
      return;
    }
    if (about || !window.location.hash) {
      window.scrollTo(0, 0);
      return;
    }
    document.querySelector(window.location.hash)?.scrollIntoView();
  }, [about, pay, productLanding, path]);

  if (pay) {
    return <PayPage />;
  }

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
      <SiteAnalytics />
    </StoreProvider>
  );
}
