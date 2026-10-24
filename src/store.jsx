import { createContext, useContext, useEffect, useMemo, useState } from "react";
import {
  FREE_SHIPPING,
  shippingFeeFor,
  findProduct,
  resolveOffer,
} from "./data";
import { notifyTelegramOrder } from "./notifyTelegram";
import { saveCustomer } from "./saveCustomer";
import { syncProductQuery } from "./share";

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
  const [quickViewId, setQuickViewId] = useState(() => {
    try {
      const id = new URLSearchParams(window.location.search).get("product");
      return id && findProduct(id) ? id : null;
    } catch {
      return null;
    }
  });
  const [info, setInfo] = useState(null);
  const [category, setCategory] = useState("הכל");
  const [toast, setToast] = useState(null);
  const [checkoutStep, setCheckoutStep] = useState("cart");
  const [order, setOrder] = useState(null);
  const [lastOrder, setLastOrder] = useState(null);

  useEffect(() => {
    localStorage.setItem("barbero-cart", JSON.stringify(cart));
  }, [cart]);

  useEffect(() => {
    localStorage.setItem("barbero-wishlist", JSON.stringify(wishlist));
  }, [wishlist]);

  useEffect(() => {
    syncProductQuery(quickViewId);
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
  const shipping = shippingFeeFor(subtotal);
  const total = subtotal + shipping;
  const remaining = Math.max(0, FREE_SHIPPING - subtotal);
  const progress = subtotal <= 0 ? 0 : Math.min(100, (subtotal / FREE_SHIPPING) * 100);
  const cartCount = cart.reduce((sum, line) => sum + line.qty, 0);

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
    const snapshot = {
      number: `BRB-${Math.floor(100000 + Math.random() * 900000)}`,
      createdAt: new Date().toISOString(),
      details,
      total,
      subtotal,
      shipping,
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
    setCheckoutStep("done");
    notifyTelegramOrder(snapshot);
    saveCustomer({ name: details.name, phone: details.phone });
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

  const value = {
    cart,
    lines,
    wishlist,
    cartCount,
    wishCount: wishlist.length,
    subtotal,
    shipping,
    total,
    remaining,
    progress,
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
    setCheckoutStep,
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
