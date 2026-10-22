import { useEffect, useState } from "react";
import { discountPercent, resolveOffer } from "../data";
import { useStore } from "../store";
import { IconClose, IconHeart, IconMinus, IconPlus, Stars } from "./Icons";
import Price from "./Price";
import ProductImage, { imageFrame } from "./ProductImage";

export default function QuickView() {
  const { quickView, closeQuickView, addToCart, toggleWish, isWished } = useStore();
  const [variantId, setVariantId] = useState(null);
  const [qty, setQty] = useState(1);
  const [photo, setPhoto] = useState(0);

  useEffect(() => {
    setVariantId(quickView?.variants?.[0]?.id ?? null);
    setQty(1);
    setPhoto(0);
  }, [quickView?.id]);

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

  return (
    <div className="fixed inset-0 z-[60] flex items-end justify-center sm:items-center sm:p-6">
      <button type="button" className="absolute inset-0 bg-black/75 backdrop-blur-sm" aria-label="סגירה" onClick={closeQuickView} />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="quick-view-title"
        className="relative z-10 grid max-h-[92svh] w-full max-w-4xl overflow-y-auto border border-line bg-slate sm:grid-cols-2"
      >
        <button
          type="button"
          className="icon-btn absolute top-2 left-2 z-10 bg-ink/75"
          aria-label="סגירה"
          onClick={closeQuickView}
        >
          <IconClose />
        </button>
        <div className={`relative flex min-h-72 flex-col ${frame.box}`}>
          <ProductImage
            src={activePhoto}
            alt={quickView.name}
            className={
              frame.studio
                ? "h-full max-h-[46svh] w-full flex-1 object-contain p-6 sm:max-h-none sm:min-h-0"
                : "h-full max-h-[46svh] w-full flex-1 object-cover sm:max-h-none sm:min-h-0"
            }
          />
          {gallery.length > 1 && (
            <div className="flex gap-2 p-3" role="group" aria-label="גלריית המוצר">
              {gallery.map((src, index) => (
                <button
                  key={src}
                  type="button"
                  aria-label={`תמונה ${index + 1}`}
                  aria-pressed={index === photo}
                  onClick={() => setPhoto(index)}
                  className={`h-16 w-16 overflow-hidden border ${index === photo ? "border-gold" : "border-white/20"}`}
                >
                  <img src={src} alt="" className="h-full w-full object-contain" />
                </button>
              ))}
            </div>
          )}
          {soldOut ? (
            <span className="absolute top-4 start-4 bg-ink/85 px-3 py-1 text-xs">אזל מהמלאי</span>
          ) : off > 0 ? (
            <span dir="ltr" className="absolute top-4 start-4 bg-gold px-3 py-1 text-xs font-semibold text-[#16120b]">
              -{off}%
            </span>
          ) : null}
        </div>

        <div className="flex flex-col p-5 sm:p-8">
          <p className="text-xs text-gold">{quickView.category}</p>
          <h2 id="quick-view-title" className="mt-2 font-display text-4xl leading-none">
            {quickView.name}
          </h2>
          <p className="mt-3 text-xs tracking-[0.16em] text-muted">{quickView.brand}</p>
          <div className="mt-4">
            <Stars value={quickView.rating} reviews={quickView.reviews} />
          </div>
          <div className="mt-5">
            <Price price={offer.price} compareAt={offer.compareAt} size="lg" />
          </div>
          <p className="mt-4 text-sm leading-7 text-ivory/75">{quickView.blurb}</p>

          <dl className="mt-6 grid grid-cols-2 gap-px bg-white/10 text-sm">
            {specs.map(([label, value]) => (
              <div key={label} className="bg-ink px-3 py-3">
                <dt className="text-xs text-muted">{label}</dt>
                <dd className="mt-1">{value}</dd>
              </div>
            ))}
          </dl>

          {quickView.variants && (
            <div className="mt-5" role="group" aria-label="בחירת דגם">
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

          {quickView.stock > 0 && quickView.stock <= 3 && (
            <p className="mt-4 text-sm text-gold-soft">נותרו {quickView.stock} יחידות</p>
          )}

          <div className="mt-6 flex items-center gap-3">
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
              aria-label={wished ? "הסרה מרשימת המשאלות" : "שמירה לרשימת המשאלות"}
              onClick={() => toggleWish(quickView.id)}
            >
              <IconHeart filled={wished} />
            </button>
          </div>

          <button
            type="button"
            className="btn-gold mt-4 h-12 w-full"
            disabled={soldOut}
            onClick={() => addToCart(quickView.id, qty, offer.variant?.id, { open: true })}
          >
            {soldOut ? "אזל מהמלאי" : "הוסף לעגלה"}
          </button>
        </div>
      </div>
    </div>
  );
}
