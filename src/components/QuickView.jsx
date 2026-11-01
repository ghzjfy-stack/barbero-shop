import { useEffect, useRef, useState } from "react";
import { discountPercent, FIRST_ORDER_COUPON, resolveOffer } from "../data";
import { useStore } from "../store";
import { IconChevron, IconClose, IconHeart, IconMinus, IconPlus, Stars } from "./Icons";
import Price from "./Price";
import ProductImage, { imageFrame } from "./ProductImage";
import ProductShareButton from "./ProductShareButton";
import ProductTitle from "./ProductTitle";
import PurchaseTrust from "./PurchaseTrust";
import StockUrgency from "./StockUrgency";

export default function QuickView() {
  const {
    quickView,
    closeQuickView,
    addToCart,
    toggleWish,
    isWished,
    firstOrderEligible,
    appliedCoupon,
  } = useStore();
  const [variantId, setVariantId] = useState(null);
  const [qty, setQty] = useState(1);
  const [photo, setPhoto] = useState(0);
  const touchX = useRef(null);
  const galleryLength = quickView?.images?.length || (quickView?.image ? 1 : 0);

  const stepPhoto = (delta) => {
    if (galleryLength < 2) return;
    setPhoto((current) => (current + delta + galleryLength) % galleryLength);
  };

  useEffect(() => {
    setVariantId(quickView?.variants?.[0]?.id ?? null);
    setQty(1);
    setPhoto(0);
  }, [quickView?.id]);

  useEffect(() => {
    if (!quickView || galleryLength < 2) return undefined;
    const onKey = (event) => {
      if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
      if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) return;
      event.preventDefault();
      stepPhoto(event.key === "ArrowLeft" ? 1 : -1);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [quickView, galleryLength]);

  if (!quickView) return null;

  const offer = resolveOffer(quickView, variantId);
  const wished = isWished(quickView.id);
  const soldOut = quickView.stock <= 0;
  const off = discountPercent(offer.price, offer.compareAt);
  const maxQty = Math.max(quickView.stock, 1);
  const frame = imageFrame(quickView);
  const gallery = quickView.images?.length ? quickView.images : [quickView.image];
  const activePhoto = gallery[photo] ?? gallery[0];
  const specs = [
    ["מותג", quickView.brand],
    ["קטגוריה", quickView.category],
    quickView.voltage ? ["מתח", quickView.voltage] : null,
    ["מקור", quickView.origin],
    ["מק״ט", quickView.sku],
  ].filter(Boolean);

  const addToCartNow = () => addToCart(quickView.id, qty, offer.variant?.id, { open: true });

  return (
    <div className="fixed inset-0 z-[60] flex items-end justify-center sm:items-center sm:p-6">
      <button type="button" className="absolute inset-0 bg-black/75 backdrop-blur-sm" aria-label="סגירה" onClick={closeQuickView} />
      <div role="dialog" aria-modal="true" aria-labelledby="quick-view-title" className="relative z-10 w-full max-w-4xl">
        <div className="pointer-events-none absolute inset-0 z-20" dir="ltr">
          <button
            type="button"
            className="icon-btn pointer-events-auto absolute top-2 left-2 bg-ink/80"
            aria-label="סגירה"
            onClick={closeQuickView}
          >
            <IconClose />
          </button>
        </div>
        <div className="grid max-h-[92svh] overflow-y-auto border border-line bg-slate pb-[calc(5.5rem+env(safe-area-inset-bottom,0px))] sm:grid-cols-2 sm:pb-0">
          <div className={`relative flex flex-col ${frame.box}`}>
            <div
              className="relative mx-auto aspect-square w-full max-h-[min(38svh,18rem)] sm:max-h-none"
              onTouchStart={(event) => {
                touchX.current = event.changedTouches[0]?.clientX ?? null;
              }}
              onTouchEnd={(event) => {
                if (touchX.current == null || gallery.length < 2) return;
                const dx = (event.changedTouches[0]?.clientX ?? touchX.current) - touchX.current;
                if (Math.abs(dx) < 40) return;
                stepPhoto(dx < 0 ? 1 : -1);
              }}
            >
              <ProductImage
                src={activePhoto}
                alt={`${quickView.name}, תמונה ${photo + 1} מתוך ${gallery.length}`}
                className="h-full w-full object-contain"
              />
              {/* LTR corners: close is top-left on the dialog; share stays top-right and tappable */}
              <div className="pointer-events-none absolute inset-0 z-30" dir="ltr">
                <div className="pointer-events-auto absolute top-2 right-2">
                  <ProductShareButton
                    product={quickView}
                    variantId={variantId}
                    className="grid h-11 w-11 place-items-center bg-ink/80 text-ivory transition hover:text-gold-soft"
                  />
                </div>
              </div>
              {gallery.length > 1 && (
                <>
                  <button
                    type="button"
                    className="absolute top-1/2 start-2 z-10 grid h-11 w-11 -translate-y-1/2 place-items-center bg-ink/80 text-ivory hover:text-gold-soft"
                    aria-label="התמונה הקודמת"
                    onClick={() => stepPhoto(-1)}
                  >
                    <IconChevron className="h-5 w-5 rotate-180" />
                  </button>
                  <button
                    type="button"
                    className="absolute top-1/2 end-2 z-10 grid h-11 w-11 -translate-y-1/2 place-items-center bg-ink/80 text-ivory hover:text-gold-soft"
                    aria-label="התמונה הבאה"
                    onClick={() => stepPhoto(1)}
                  >
                    <IconChevron className="h-5 w-5" />
                  </button>
                  <p className="pointer-events-none absolute inset-x-0 bottom-3 flex justify-center">
                    <span dir="ltr" className="bg-ink/80 px-2 py-1 text-[11px] tabular-nums text-ivory">
                      {photo + 1} / {gallery.length}
                    </span>
                  </p>
                </>
              )}
            </div>
            {gallery.length > 1 && (
              <div className="hidden gap-2 overflow-x-auto p-3 sm:flex" role="group" aria-label="גלריית המוצר">
                {gallery.map((src, index) => (
                  <button
                    key={src}
                    type="button"
                    aria-label={`תמונה ${index + 1} מתוך ${gallery.length}`}
                    aria-pressed={index === photo}
                    onClick={() => setPhoto(index)}
                    className={`h-16 w-16 shrink-0 overflow-hidden border ${index === photo ? "border-gold" : "border-white/20"}`}
                  >
                    <img src={src} alt="" className="h-full w-full object-contain" />
                  </button>
                ))}
              </div>
            )}
            {soldOut ? (
              <span className="absolute top-4 start-4 bg-ink/85 px-3 py-1 text-xs">אזל מהמלאי</span>
            ) : quickView.badge ? (
              <span className="absolute top-4 start-4 max-w-[70%] bg-ink/85 px-3 py-1 text-start text-xs leading-5 text-gold-soft">
                {quickView.badge}
              </span>
            ) : off > 0 ? (
              <span dir="ltr" className="absolute top-4 start-4 bg-gold px-3 py-1 text-xs font-semibold text-[#16120b]">
                -{off}%
              </span>
            ) : null}
          </div>

          <div className="flex flex-col p-4 sm:p-8">
            <p className="text-xs text-gold">{quickView.category}</p>
            <h2 id="quick-view-title" className="mt-1.5 text-start font-display text-[1.45rem] leading-tight sm:mt-2 sm:text-4xl">
              <ProductTitle product={quickView} />
            </h2>
            <p className="mt-2 text-xs tracking-[0.16em] text-muted sm:mt-3">{quickView.brand}</p>
            {typeof quickView.rating === "number" && (
              <div className="mt-2 sm:mt-4">
                <Stars value={quickView.rating} reviews={quickView.reviews} />
              </div>
            )}

            {/* Price + buy first — visible on ad landings without scrolling past the image */}
            <div className="mt-3 sm:mt-5">
              <Price price={offer.price} compareAt={offer.compareAt} size="lg" />
            </div>
            {quickView.excludeFirstOrderCoupon || quickView.freeShipping ? (
              <p className="mt-2 text-[12px] leading-5 text-gold-soft">
                {quickView.badge ? `${quickView.badge} · ` : ""}
                <span className="font-semibold tabular-nums" dir="ltr">
                  ₪{offer.price.toLocaleString("he-IL")}
                </span>
                <span className="text-muted"> עד הבית · משלוח חינם</span>
              </p>
            ) : firstOrderEligible ? (
              <p className="mt-2 text-[12px] leading-5 text-gold-soft">
                עם קופון{" "}
                <span className="font-semibold tracking-wide" dir="ltr">
                  {appliedCoupon || FIRST_ORDER_COUPON.code}
                </span>
                :{" "}
                <span className="font-semibold tabular-nums" dir="ltr">
                  ₪
                  {Math.max(0, offer.price - FIRST_ORDER_COUPON.amount).toLocaleString("he-IL")}
                </span>
                <span className="text-muted"> כולל משלוח חינם עד הבית</span>
              </p>
            ) : (
              <p className="mt-2 text-[12px] leading-5 text-muted">משלוח חינם מ־₪499</p>
            )}
            {(quickView.excludeFirstOrderCoupon || quickView.freeShipping) && !soldOut ? (
              <StockUrgency stock={quickView.stock} className="mt-3" />
            ) : null}
            <PurchaseTrust className="mt-2.5" />

            {quickView.variants && (
              <div className="mt-4" role="group" aria-label="בחירת דגם">
                <p className="mb-2 text-xs text-muted">דגם</p>
                <div className="flex flex-wrap gap-2">
                  {quickView.variants.map((variant) => (
                    <button
                      key={variant.id}
                      type="button"
                      aria-pressed={variantId === variant.id}
                      disabled={soldOut}
                      onClick={() => setVariantId(variant.id)}
                      className={`border px-3 py-2 text-sm ${
                        variantId === variant.id
                          ? "border-gold bg-gold text-[#16120b]"
                          : "border-white/15"
                      }`}
                    >
                      {variant.label}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {!(quickView.excludeFirstOrderCoupon || quickView.freeShipping) &&
              quickView.stock > 0 &&
              quickView.stock <= 3 && (
              <p className="mt-3 text-sm text-gold-soft">נותרו {quickView.stock} יחידות</p>
            )}

            <div className="mt-4 flex items-center gap-3">
              <div className="flex border border-white/15">
                <button
                  type="button"
                  className="grid h-12 w-12 place-items-center"
                  aria-label="הפחתת כמות"
                  onClick={() => setQty((value) => Math.max(1, value - 1))}
                  disabled={soldOut}
                >
                  <IconMinus className="h-4 w-4" />
                </button>
                <span className="grid h-12 w-10 place-items-center tabular-nums" aria-live="polite">
                  {qty}
                </span>
                <button
                  type="button"
                  className="grid h-12 w-12 place-items-center"
                  aria-label="הגדלת כמות"
                  onClick={() => setQty((value) => Math.min(maxQty, value + 1))}
                  disabled={soldOut || qty >= quickView.stock}
                >
                  <IconPlus className="h-4 w-4" />
                </button>
              </div>
              <button
                type="button"
                className={`grid h-12 w-12 place-items-center border border-white/15 ${wished ? "text-gold" : ""}`}
                aria-pressed={wished}
                aria-label={wished ? "הסרה מהמועדפים שלי" : "הוספה למועדפים שלי"}
                onClick={() => toggleWish(quickView.id)}
              >
                <IconHeart filled={wished} />
              </button>
            </div>

            <button
              type="button"
              className="btn-gold mt-3 hidden h-12 w-full sm:inline-flex"
              disabled={soldOut}
              onClick={addToCartNow}
            >
              {soldOut ? "אזל מהמלאי" : "הוסף לעגלה"}
            </button>

            <p className="mt-5 text-sm leading-7 text-ivory/75 sm:mt-4">{quickView.blurb}</p>
            {quickView.features?.length > 0 && (
              <ul className="mt-4 list-disc space-y-2 ps-5 text-sm leading-7 text-ivory/75">
                {quickView.features.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            )}

            <dl className="mt-6 grid grid-cols-1 gap-px bg-white/10 text-sm min-[480px]:grid-cols-2">
              {specs.map(([label, value]) => (
                <div key={label} className="bg-ink px-3 py-3">
                  <dt className="text-xs text-muted">{label}</dt>
                  <dd className="mt-1 break-words">{value}</dd>
                </div>
              ))}
            </dl>
          </div>
        </div>

        {/* Sticky buy bar — mobile ad landings always see price + CTA */}
        <div className="absolute inset-x-0 bottom-0 z-30 border-t border-white/10 bg-slate/95 px-4 py-3 backdrop-blur-md sm:hidden pb-[max(0.75rem,env(safe-area-inset-bottom,0px))]">
          <div className="flex items-center gap-3">
            <div className="min-w-0 flex-1">
              <Price price={offer.price} compareAt={offer.compareAt} />
            </div>
            <button
              type="button"
              className="btn-gold h-12 shrink-0 px-5 text-sm"
              disabled={soldOut}
              onClick={addToCartNow}
            >
              {soldOut ? "אזל" : "הוסף לעגלה"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
