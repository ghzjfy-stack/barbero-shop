import { createContext, useContext, useEffect, useMemo, useState } from "react";
import {
  FIRST_ORDER_COUPON,
  FREE_SHIPPING,
  isFirstOrderCouponCode,
  normalizeCouponCode,
  shippingFeeFor,
  findProduct,
  resolveOffer,
} from "./data";

const HAS_ORDERED_KEY = "barbero-has-ordered";
const COUPON_KEY = "barbero-coupon";

function readHasOrdered() {
  try {
    return localStorage.getItem(HAS_ORDERED_KEY) === "1";
  } catch {
    return false;
  }
}

function readSavedCoupon() {
  try {
    const code = normalizeCouponCode(localStorage.getItem(COUPON_KEY) || "");
    return isFirstOrderCouponCode(code) ? code : "";
  } catch {
    return "";
  }
}
import { notifyTelegramOrder } from "./notifyTelegram";
import { notifyOrderEmail } from "./notifyOrderEmail";
import { notifySheetsOrder } from "./notifySheetsOrder";
import { saveCustomer } from "./saveCustomer";
import { notifySupabaseOrder } from "./notifySupabaseOrder";
import { parseProductFromLocation, syncProductLocation } from "./share";
import {
  trackMetaAddToCart,
  trackMetaInitiateCheckout,
  trackMetaViewContent,
} from "./metaPixel";

const StoreContext = createContext(null);

function readStorage(key, fallback) {
  try {
    const raw = JSON.parse(localStorage.getItem(key) || "");
    return Array.isArray(raw) ? raw : fallback;
  } catch {
    return fallback;
  }
}

export function StoreProvider({ children }) {
  const [cart, setCart] = useState(() =>
    readStorage("barbero-cart", []).filter(
      (line) => line?.id && line.qty > 0 && findProduct(line.id),
    ),
  );
  const [wishlist, setWishlist] = useState(() =>
    readStorage("barbero-wishlist", []).filter((id) => findProduct(id)),
  );
  const [cartOpen, setCartOpen] = useState(false);
  const [wishOpen, setWishOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [quickViewId, setQuickViewId] = useState(() => parseProductFromLocation());
  const [info, setInfo] = useState(null);
  const [category, setCategory] = useState("הכל");
  const [toast, setToast] = useState(null);
  const [checkoutStep, setCheckoutStep] = useState("cart");
  const [order, setOrder] = useState(null);
  const [lastOrder, setLastOrder] = useState(null);
  // Auto-seed first-order coupon for eligible visitors (ads / cold land) —
  // discount + free shipping apply as soon as the cart has items.
  const [appliedCoupon, setAppliedCoupon] = useState(() => {
    if (readHasOrdered()) return "";
    return readSavedCoupon() || FIRST_ORDER_COUPON.code;
  });
  const [couponError, setCouponError] = useState("");

  useEffect(() => {
    localStorage.setItem("barbero-cart", JSON.stringify(cart));
  }, [cart]);

  useEffect(() => {
    localStorage.setItem("barbero-wishlist", JSON.stringify(wishlist));
  }, [wishlist]);

  useEffect(() => {
    try {
      if (appliedCoupon) localStorage.setItem(COUPON_KEY, appliedCoupon);
      else localStorage.removeItem(COUPON_KEY);
    } catch {
      /* ignore quota */
    }
  }, [appliedCoupon]);

  useEffect(() => {
    syncProductLocation(quickViewId);
  }, [quickViewId]);

  // Keep modal in sync when browser back/forward hits `/p/:id`
  useEffect(() => {
    const onPop = () => setQuickViewId(parseProductFromLocation());
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  // ViewContent on every product open — including cold land from ad `/p/:id`
  useEffect(() => {
    if (!quickViewId) return;
    const product = findProduct(quickViewId);
    if (product) trackMetaViewContent(product, resolveOffer(product));
  }, [quickViewId]);

  useEffect(() => {
    if (!toast) return undefined;
    const timer = setTimeout(() => setToast(null), 3400);
    return () => clearTimeout(timer);
  }, [toast]);

  useEffect(() => {
    const locked =
      cartOpen || wishOpen || searchOpen || menuOpen || quickViewId || info;
    document.body.style.overflow = locked ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [cartOpen, wishOpen, searchOpen, menuOpen, quickViewId, info]);

  useEffect(() => {
    const onKey = (event) => {
      if (event.key !== "Escape") return;
      if (menuOpen) setMenuOpen(false);
      else if (searchOpen) setSearchOpen(false);
      else if (quickViewId) setQuickViewId(null);
      else if (info) setInfo(null);
      else if (wishOpen) setWishOpen(false);
      else if (cartOpen) setCartOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [menuOpen, searchOpen, quickViewId, info, wishOpen, cartOpen]);

  useEffect(() => {
    const onResize = () => {
      if (window.innerWidth >= 768) setMenuOpen(false);
    };
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  const lines = useMemo(
    () =>
      cart
        .map((line) => {
          const product = findProduct(line.id);
          if (!product) return null;
          const offer = resolveOffer(product, line.variantId);
          return {
            ...line,
            product,
            offer,
            lineTotal: offer.price * line.qty,
          };
        })
        .filter(Boolean),
    [cart],
  );

  const subtotal = lines.reduce((sum, line) => sum + line.lineTotal, 0);
  const firstOrderEligible = !readHasOrdered() && !lastOrder;
  const couponValid =
    Boolean(appliedCoupon) &&
    isFirstOrderCouponCode(appliedCoupon) &&
    firstOrderEligible &&
    subtotal > 0;
  const discount = couponValid ? Math.min(FIRST_ORDER_COUPON.amount, subtotal) : 0;
  const shipping = shippingFeeFor(subtotal, { waive: couponValid });
  const total = Math.max(0, subtotal - discount) + shipping;
  const remaining = couponValid ? 0 : Math.max(0, FREE_SHIPPING - subtotal);
  const progress = couponValid
    ? 100
    : subtotal <= 0
      ? 0
      : Math.min(100, (subtotal / FREE_SHIPPING) * 100);
  const cartCount = cart.reduce((sum, line) => sum + line.qty, 0);
  const freeShippingReason = couponValid
    ? "coupon"
    : subtotal > 0 && shipping === 0
      ? "threshold"
      : null;

  const applyCoupon = (rawCode, { quiet = false } = {}) => {
    const code = normalizeCouponCode(rawCode);
    setCouponError("");
    if (!code) {
      setCouponError("הזינו קוד קופון");
      return false;
    }
    if (!isFirstOrderCouponCode(code)) {
      setCouponError("קוד לא תקין");
      return false;
    }
    if (!firstOrderEligible) {
      setCouponError("הקוד להזמנה ראשונה בלבד");
      return false;
    }
    setAppliedCoupon(code);
    if (!quiet && subtotal > 0) {
      notify(`הקופון הוחל — ₪${FIRST_ORDER_COUPON.amount} הנחה + משלוח חינם`);
    } else if (!quiet && subtotal <= 0) {
      notify("הקופון מוכן — יוחל בעגלה עם משלוח חינם");
    }
    return true;
  };

  const clearCoupon = () => {
    setAppliedCoupon("");
    setCouponError("");
  };

  const notify = (message, action = null) => {
    setToast({ id: Date.now(), message, action });
  };

  const closeTransient = () => {
    setCartOpen(false);
    setWishOpen(false);
    setSearchOpen(false);
    setMenuOpen(false);
    setQuickViewId(null);
  };

  const addToCart = (productId, qty = 1, variantId, options = {}) => {
    const product = findProduct(productId);
    if (!product || product.stock <= 0) {
      notify("הדגם אזל מהמלאי");
      return;
    }

    const offer = resolveOffer(product, variantId);
    const vid = offer.variant?.id ?? "default";
    const current = cart.find((line) => line.id === product.id && line.variantId === vid)?.qty ?? 0;

    if (current >= product.stock) {
      notify("הגעתם לכמות הזמינה");
      return;
    }

    const nextQty = Math.min(product.stock, current + qty);
    setCart((currentLines) => {
      const index = currentLines.findIndex(
        (line) => line.id === product.id && line.variantId === vid,
      );
      if (index >= 0) {
        return currentLines.map((line, lineIndex) =>
          lineIndex === index ? { ...line, qty: nextQty } : line,
        );
      }
      return [...currentLines, { id: product.id, variantId: vid, qty: nextQty }];
    });
    setCheckoutStep("cart");
    setOrder(null);

    trackMetaAddToCart(product, offer, Math.max(1, nextQty - current));

    if (options.open) {
      setWishOpen(false);
      setSearchOpen(false);
      setMenuOpen(false);
      setQuickViewId(null);
      setInfo(null);
      setCartOpen(true);
      return;
    }

    notify(`${product.name} נוסף לעגלה`, "cart");
  };

  const setQty = (productId, variantId, qty) => {
    const product = findProduct(productId);
    const max = product?.stock ?? 1;
    setCart((currentLines) => {
      if (qty <= 0) {
        return currentLines.filter(
          (line) => !(line.id === productId && line.variantId === variantId),
        );
      }
      return currentLines.map((line) =>
        line.id === productId && line.variantId === variantId
          ? { ...line, qty: Math.min(max, qty) }
          : line,
      );
    });
  };

  const removeLine = (productId, variantId) => {
    setCart((currentLines) =>
      currentLines.filter(
        (line) => !(line.id === productId && line.variantId === variantId),
      ),
    );
    notify("הפריט הוסר מהעגלה");
  };

  const toggleWish = (productId) => {
    const exists = wishlist.includes(productId);
    setWishlist((current) =>
      exists ? current.filter((id) => id !== productId) : [...current, productId],
    );
    notify(
      exists ? "המוצר הוסר מהמועדפים שלי" : "המוצר נוסף בהצלחה למועדפים שלי",
      exists ? null : "wish",
    );
  };

  const openCart = () => {
    closeTransient();
    setCartOpen(true);
    if (cart.length === 0 && checkoutStep !== "done") setCheckoutStep("cart");
  };

  const openWish = () => {
    closeTransient();
    setWishOpen(true);
  };

  const openSearch = () => {
    closeTransient();
    setSearchOpen(true);
  };

  const openQuickView = (productId) => {
    closeTransient();
    setQuickViewId(productId);
  };

  const openInfo = (pageId) => {
    setSearchOpen(false);
    setMenuOpen(false);
    setQuickViewId(null);
    setInfo(pageId);
  };

  const placeOrder = (details) => {
    const payment = details?.payment === "paypal" ? "paypal" : "bit";
    const couponNote =
      discount > 0 && appliedCoupon
        ? `קופון ${appliedCoupon}: −₪${discount} (הזמנה ראשונה)`
        : "";
    const notes = [details?.notes, couponNote].filter(Boolean).join(" · ");
    const snapshot = {
      number: `BRB-${Math.floor(100000 + Math.random() * 900000)}`,
      createdAt: new Date().toISOString(),
      details: { ...details, notes },
      payment,
      total,
      subtotal,
      shipping,
      discount,
      coupon: discount > 0 ? appliedCoupon : "",
      lines: lines.map((line) => ({
        id: line.product.id,
        name: line.product.name,
        kind: line.product.kind,
        model: line.product.model,
        label: line.offer.label,
        variantId: line.variantId,
        qty: line.qty,
        unitPrice: line.offer.price,
        lineTotal: line.lineTotal,
      })),
    };
    setOrder(snapshot);
    setLastOrder(snapshot);
    setCart([]);
    setAppliedCoupon("");
    setCouponError("");
    try {
      localStorage.setItem(HAS_ORDERED_KEY, "1");
      localStorage.removeItem(COUPON_KEY);
    } catch {
      /* ignore */
    }
    setCheckoutStep("done");
    // Purchase pixel fires only after real payment (Bit/PayPal confirm or ops «שולם»).
    notifyTelegramOrder(snapshot);
    notifySheetsOrder(snapshot);
    notifySupabaseOrder(snapshot);
    notifyOrderEmail(snapshot);
    saveCustomer({
      name: details.name,
      phone: details.phone,
      email: details.email,
      city: details.city,
      address: details.address,
      unit: details.unit,
      postal: details.postal,
      notes: details.notes,
      last_order_number: snapshot.number,
    });
  };

  const finishCheckout = () => {
    setOrder(null);
    setCheckoutStep("cart");
    setCartOpen(false);
  };

  const goToCategory = (next) => {
    setCategory(next || "הכל");
    setMenuOpen(false);
  };

  const goToCheckoutStep = (step) => {
    if (step === "details" && checkoutStep !== "details") {
      trackMetaInitiateCheckout({
        value: total,
        numItems: cartCount,
        contentIds: lines.map((line) => line.product.id),
      });
    }
    setCheckoutStep(step);
  };

  const value = {
    cart,
    lines,
    wishlist,
    cartCount,
    wishCount: wishlist.length,
    subtotal,
    shipping,
    discount,
    total,
    remaining,
    progress,
    freeShippingReason,
    appliedCoupon,
    couponError,
    applyCoupon,
    clearCoupon,
    firstOrderEligible,
    cartOpen,
    wishOpen,
    searchOpen,
    menuOpen,
    setMenuOpen,
    quickView: findProduct(quickViewId),
    info,
    category,
    setCategory,
    toast,
    dismissToast: () => setToast(null),
    checkoutStep,
    setCheckoutStep: goToCheckoutStep,
    order,
    lastOrder,
    addToCart,
    setQty,
    removeLine,
    toggleWish,
    isWished: (id) => wishlist.includes(id),
    openCart,
    closeCart: () => setCartOpen(false),
    openWish,
    closeWish: () => setWishOpen(false),
    openSearch,
    closeSearch: () => setSearchOpen(false),
    openQuickView,
    closeQuickView: () => setQuickViewId(null),
    openInfo,
    closeInfo: () => setInfo(null),
    placeOrder,
    finishCheckout,
    goToCategory,
  };

  return <StoreContext.Provider value={value}>{children}</StoreContext.Provider>;
}

export function useStore() {
  const context = useContext(StoreContext);
  if (!context) throw new Error("useStore must be used within StoreProvider");
  return context;
}
