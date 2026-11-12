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
import FeedbackInvite from "./components/FeedbackInvite";
import About from "./components/About";
import Footer from "./components/Footer";
import CartDrawer from "./components/CartDrawer";
import WishlistDrawer from "./components/WishlistDrawer";
import SearchModal from "./components/SearchModal";
import QuickView from "./components/QuickView";
import InfoDialog from "./components/InfoDialog";
import Toast from "./components/Toast";
import FacebookButton from "./components/FacebookButton";
import WhatsAppButton from "./components/WhatsAppButton";
import PayPage from "./components/PayPage";
import SiteAnalytics from "./components/SiteAnalytics";

const HOME_TITLE = "BARBERO | עיצוב שיער וגרומינג פרימיום ביבוא ישיר מארה״ב";
const HOME_DESCRIPTION =
  "ציוד פרימיום לעיצוב שיער, גילוח וגרומינג ביבוא ישיר מארה״ב. דגמים נבחרים שלא תמצאו בכל חנות, אחריות יבואן 12 חודשים ומשלוח חינם מ־₪499 לכל הארץ.";
const ABOUT_DESCRIPTION =
  "BARBERO — יבוא ישיר מארה״ב של ציוד פרימיום לעיצוב שיער, גילוח וגרומינג. למספרות, למעצבות ולבית, עם אחריות יבואן ושירות ישירות מולנו.";

function setMetaDescription(content) {
  const node = document.querySelector('meta[name="description"]');
  if (node) node.setAttribute("content", content);
  const og = document.querySelector('meta[property="og:description"]');
  if (og) og.setAttribute("content", content);
}

function Shell() {
  const path = usePathname();
  const about = path === "/about";
  const pay = path === "/pay";
  const productLanding = /^\/p\//.test(path);

  useEffect(() => {
    const landedProduct = productLanding ? findProduct(parseProductFromLocation()) : null;
    if (pay) {
      document.title = "תשלום הזמנה | BARBERO";
      setMetaDescription(HOME_DESCRIPTION);
    } else if (about) {
      document.title = "BARBERO | אודות";
      setMetaDescription(ABOUT_DESCRIPTION);
    } else if (landedProduct) {
      document.title = `${landedProduct.name} | BARBERO`;
      setMetaDescription(landedProduct.blurb || HOME_DESCRIPTION);
    } else {
      document.title = HOME_TITLE;
      setMetaDescription(HOME_DESCRIPTION);
    }
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
    const target = document.querySelector(window.location.hash);
    target?.scrollIntoView({ behavior: "smooth", block: "start" });
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
            <FeedbackInvite />
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
      <FacebookButton />
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
