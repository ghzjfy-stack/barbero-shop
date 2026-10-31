import { useState } from "react";
import { FIRST_ORDER_COUPON, FREE_SHIPPING, formatPrice } from "../data";
import { trackMetaAddPaymentInfo } from "../metaPixel";
import { openPayPalPayment } from "../payment";
import { useStore } from "../store";
import BitPayPanel from "./BitPayPanel";
import Drawer from "./Drawer";
import { IconClose, IconMinus, IconPlus, IconTrash } from "./Icons";
import ProductImage, { imageFrame } from "./ProductImage";
import ProductTitle from "./ProductTitle";
import PurchaseTrust from "./PurchaseTrust";

const emptyDetails = {
  name: "",
  phone: "",
  email: "",
  city: "",
  address: "",
  unit: "",
  postal: "",
  notes: "",
  agree: false,
  payment: "bit",
};

function isValidEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(value || "").trim());
}

export default function CartDrawer() {
  const store = useStore();
  const [details, setDetails] = useState(emptyDetails);
  const [errors, setErrors] = useState({});
  const [copied, setCopied] = useState(false);
  const [couponDraft, setCouponDraft] = useState("");

  const setField = (key, value) => {
    setDetails((current) => ({ ...current, [key]: value }));
    setErrors((current) => ({ ...current, [key]: undefined }));
  };

  const validate = () => {
    const next = {};
    if (details.name.trim().length < 2) next.name = "נשמח לשם מלא";
    const phone = details.phone.replace(/[^\d]/g, "");
    if (phone.length < 9 || phone.length > 13) next.phone = "מספר טלפון לא תקין";
    if (!isValidEmail(details.email)) next.email = "כתובת אימייל לא תקינה";
    if (details.city.trim().length < 2) next.city = "חסרה עיר";
    if (details.address.trim().length < 4) next.address = "חסרה כתובת למשלוח";
    const postal = details.postal.trim();
    if (postal && !/^\d{5}(\d{2})?$/.test(postal)) next.postal = "מיקוד לא תקין";
    if (!details.agree) next.agree = "יש לאשר את התקנון כדי להמשיך";
    if (details.payment !== "bit" && details.payment !== "paypal") next.payment = "בחרו אמצעי תשלום";
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const submit = (event) => {
    event.preventDefault();
    if (!validate()) return;
    store.placeOrder({
      name: details.name.trim(),
      phone: details.phone.trim(),
      email: details.email.trim().toLowerCase(),
      city: details.city.trim(),
      address: details.address.trim(),
      unit: details.unit.trim(),
      postal: details.postal.trim(),
      notes: details.notes.trim(),
      payment: details.payment,
    });
    setDetails(emptyDetails);
    setCopied(false);
  };

  const copyNumber = async () => {
    if (!store.order) return;
    try {
      await navigator.clipboard.writeText(store.order.number);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  };

  const startPayment = () => {
    if (!store.order) return;
    trackMetaAddPaymentInfo(store.order);
    if (store.order.payment === "paypal") openPayPalPayment(store.order);
  };

  const isPaypal = store.order?.payment === "paypal";

  return (
    <Drawer open={store.cartOpen} onClose={store.closeCart} label="עגלת קניות">
      <div id="cart-drawer" className="flex h-full flex-col">
        <header className="flex items-center justify-between border-b border-white/10 px-5 py-4">
          <div>
            <p className="text-[11px] text-gold">BARBERO</p>
            <h2 className="font-display text-3xl leading-none">
              {store.checkoutStep === "done" ? "תשלום" : "העגלה"}
            </h2>
          </div>
          <button type="button" className="icon-btn" aria-label="סגירת העגלה" onClick={store.closeCart}>
            <IconClose />
          </button>
        </header>

        {store.checkoutStep !== "done" && (
          <ol className="grid grid-cols-2 border-b border-white/10 text-center text-xs">
            {[
              ["cart", "עגלה"],
              ["details", "פרטי משלוח"],
            ].map(([id, label], index) => {
              const active = store.checkoutStep === id || (id === "cart" && store.checkoutStep === "details");
              const current = store.checkoutStep === id;
              return (
                <li key={id} className={`py-3 ${current ? "text-gold-soft" : "text-muted"}`} aria-current={current ? "step" : undefined}>
                  <span className={active ? "text-gold" : ""}>0{index + 1}</span>
                  <span className="mx-2">{label}</span>
                </li>
              );
            })}
          </ol>
        )}

        {store.checkoutStep === "done" && store.order ? (
          <div className="flex flex-1 flex-col overflow-y-auto px-5 py-6">
            <p className="text-sm text-muted">תודה, {store.order.details.name}</p>
            <p className="mt-1 text-sm leading-6 text-ivory/80">צעד אחרון — תשלום קצר וסיימנו</p>

            <div className="mt-5">
              {isPaypal ? (
                <div>
                  <div className="text-center">
                    <p className="text-xs tracking-wide text-muted">לתשלום ב-PayPal</p>
                    <p className="mt-2 font-display text-5xl leading-none text-gold-soft tabular-nums" dir="ltr">
                      {formatPrice(store.order.total)}
                    </p>
                  </div>
                  <button
                    type="button"
                    className="mt-6 inline-flex h-14 w-full items-center justify-center gap-2 bg-[#0070ba] text-base font-semibold text-white transition hover:bg-[#005ea6]"
                    onClick={startPayment}
                  >
                    <PayPalMark className="h-4 w-auto brightness-0 invert" />
                    שלם עכשיו ב-PayPal
                  </button>
                </div>
              ) : (
                <BitPayPanel order={store.order} />
              )}
            </div>

            <details className="group mt-8 border-t border-white/10 pt-4">
              <summary className="cursor-pointer list-none text-sm text-muted transition hover:text-ivory [&::-webkit-details-marker]:hidden">
                <span className="inline-flex w-full items-center justify-between gap-3">
                  פרטי הזמנה
                  <span className="text-xs text-gold-soft group-open:hidden">הצג</span>
                  <span className="hidden text-xs text-gold-soft group-open:inline">הסתר</span>
                </span>
              </summary>
              <div className="mt-4 space-y-4">
                <div className="flex items-center justify-between gap-3 text-sm">
                  <span className="text-muted">מספר הזמנה</span>
                  <button type="button" className="text-gold-soft underline-offset-2 hover:underline" dir="ltr" onClick={copyNumber}>
                    {copied ? "הועתק" : store.order.number}
                  </button>
                </div>
                <Totals
                  subtotal={store.order.subtotal}
                  shipping={store.order.shipping}
                  discount={store.order.discount || 0}
                  coupon={store.order.coupon || ""}
                  total={store.order.total}
                />
                <ul className="space-y-2 text-sm">
                  {store.order.lines.map((line) => (
                    <li key={`${line.name}-${line.label || ""}`} className="flex justify-between gap-4">
                      <span>
                        {line.kind && line.model ? <ProductTitle product={line} /> : line.name}
                        {line.label ? ` · ${line.label}` : ""} × {line.qty}
                      </span>
                      <span className="tabular-nums">{formatPrice(line.lineTotal)}</span>
                    </li>
                  ))}
                </ul>
                <p className="text-sm text-muted">
                  {[store.order.details.address, store.order.details.unit, store.order.details.city, store.order.details.postal]
                    .filter(Boolean)
                    .join(", ")}
                </p>
                {store.order.details.email ? (
                  <p className="text-sm text-muted">אימייל לאישור: {store.order.details.email}</p>
                ) : null}
                {store.order.details.notes ? <p className="text-sm leading-6 text-muted">{store.order.details.notes}</p> : null}
                {!isPaypal ? (
                  <div className="border border-white/10 bg-black/30 px-4 py-4 text-center">
                    <p className="text-xs text-muted">אפשר גם לסרוק מתוך ביט</p>
                    <img
                      className="mx-auto mt-3 block max-w-[160px] rounded-md bg-white p-2"
                      src="/bit-qr.jpg"
                      alt="קוד QR לתשלום ב-Bit"
                      width="160"
                    />
                  </div>
                ) : null}
              </div>
            </details>

            <button type="button" className="btn-ghost mt-6 h-11" onClick={store.finishCheckout}>
              סגור והמשך בקניות
            </button>
          </div>
        ) : store.checkoutStep === "details" ? (
          <form className="flex flex-1 flex-col overflow-y-auto px-5 py-5" onSubmit={submit} noValidate>
            <Field label="שם מלא" error={errors.name}>
              <input className="field" autoComplete="name" value={details.name} onChange={(event) => setField("name", event.target.value)} />
            </Field>
            <Field label="טלפון" error={errors.phone}>
              <input className="field" inputMode="tel" autoComplete="tel" value={details.phone} onChange={(event) => setField("phone", event.target.value)} />
            </Field>
            <Field label="אימייל" error={errors.email}>
              <input
                className="field"
                type="email"
                inputMode="email"
                autoComplete="email"
                placeholder="לאישור הזמנה"
                value={details.email}
                onChange={(event) => setField("email", event.target.value)}
              />
            </Field>
            <Field label="עיר" error={errors.city}>
              <input className="field" autoComplete="address-level2" value={details.city} onChange={(event) => setField("city", event.target.value)} />
            </Field>
            <Field label="כתובת" error={errors.address}>
              <input className="field" autoComplete="street-address" value={details.address} onChange={(event) => setField("address", event.target.value)} />
            </Field>
            <Field label="דירה / קומה / כניסה" error={errors.unit}>
              <input className="field" autoComplete="address-line2" value={details.unit} onChange={(event) => setField("unit", event.target.value)} />
            </Field>
            <Field label="מיקוד" error={errors.postal}>
              <input
                className="field"
                inputMode="numeric"
                autoComplete="postal-code"
                value={details.postal}
                onChange={(event) => setField("postal", event.target.value)}
              />
            </Field>
            <Field label="הערות לשליח" error={errors.notes}>
              <textarea
                className="field min-h-24 resize-y"
                rows={3}
                value={details.notes}
                onChange={(event) => setField("notes", event.target.value)}
              />
            </Field>

            <fieldset className="mb-3">
              <legend className="mb-2 text-sm text-muted">אמצעי תשלום</legend>
              <div className="grid grid-cols-2 gap-2" role="radiogroup" aria-label="אמצעי תשלום">
                <PaymentOption
                  selected={details.payment === "bit"}
                  onSelect={() => setField("payment", "bit")}
                  title="ביט"
                  subtitle="העברה מהירה"
                  mark={<BitMark />}
                  accent="gold"
                />
                <PaymentOption
                  selected={details.payment === "paypal"}
                  onSelect={() => setField("payment", "paypal")}
                  title="PayPal"
                  subtitle="כרטיס או יתרה"
                  mark={<PayPalMark className="h-4 w-auto text-[#79c3fc]" />}
                  accent="paypal"
                />
              </div>
              {errors.payment && <p className="mt-2 text-xs text-[#e7b2a4]">{errors.payment}</p>}
            </fieldset>

            <label className="mt-2 flex items-start gap-3 text-sm leading-6 text-muted">
              <input
                type="checkbox"
                className="mt-1 accent-[#c6a15b]"
                checked={details.agree}
                onChange={(event) => setField("agree", event.target.checked)}
              />
              <span>
                קראתי את{" "}
                <button type="button" className="text-gold-soft underline-offset-4 hover:underline" onClick={() => store.openInfo("terms")}>
                  התקנון
                </button>{" "}
                ואני מאשר/ת את פרטי ההזמנה.
              </span>
            </label>
            {errors.agree && <p className="mt-2 text-xs text-[#e7b2a4]">{errors.agree}</p>}
            <p className="mt-4 text-xs leading-6 text-muted">
              אחרי אישור ההזמנה תועברו לתשלום ב{details.payment === "paypal" ? "-PayPal" : "ביט"}. התשלום מתבצע ישירות באפליקציה / באתר של ספק התשלום.
            </p>
            <div className="mt-auto pt-6">
              <ShippingProgress
                subtotal={store.subtotal}
                remaining={store.remaining}
                progress={store.progress}
                freeReason={store.freeShippingReason}
              />
              <Totals
                subtotal={store.subtotal}
                shipping={store.shipping}
                discount={store.discount}
                coupon={store.appliedCoupon}
                total={store.total}
              />
              <div className="mt-4 grid gap-2">
                <button type="submit" className="btn-gold h-12">
                  אישור הזמנה · {formatPrice(store.total)}
                </button>
                <button type="button" className="btn-ghost h-11" onClick={() => store.setCheckoutStep("cart")}>
                  חזרה לעגלה
                </button>
              </div>
              <PurchaseTrust className="mt-3" />
            </div>
          </form>
        ) : (
          <>
            <div className="flex-1 overflow-y-auto px-5 py-4">
              {store.lines.length === 0 ? (
                <div className="grid min-h-full place-items-center py-16 text-center">
                  <div>
                    <p className="font-display text-4xl">העגלה ריקה</p>
                    <p className="mt-3 text-sm leading-7 text-muted">בחרו דגם מהקולקציה והוא יופיע כאן.</p>
                    <a href="#collection" className="btn-gold mt-6 h-11 px-6 text-sm" onClick={store.closeCart}>
                      לקולקציה
                    </a>
                  </div>
                </div>
              ) : (
                <ul className="space-y-4">
                  {store.lines.map((line) => (
                    <li key={`${line.id}-${line.variantId}`} className="grid grid-cols-[4.5rem_1fr] gap-3 border-b border-white/10 pb-4">
                      <div className={`h-24 overflow-hidden ${imageFrame(line.product).box}`}>
                        <ProductImage
                          src={line.product.image}
                          alt=""
                          className={
                            imageFrame(line.product).studio
                              ? "h-full w-full object-contain p-1.5"
                              : "h-full w-full object-cover"
                          }
                        />
                      </div>
                      <div>
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <h3 className="text-start text-sm leading-5">
                              <ProductTitle product={line.product} />
                            </h3>
                            {line.offer.label && <p className="mt-1 text-xs text-gold">{line.offer.label}</p>}
                          </div>
                          <button
                            type="button"
                            className="text-muted hover:text-ivory"
                            aria-label={`הסרת ${line.product.name}`}
                            onClick={() => store.removeLine(line.id, line.variantId)}
                          >
                            <IconTrash className="h-4 w-4" />
                          </button>
                        </div>
                        <div className="mt-3 flex items-center justify-between">
                          <div className="flex border border-white/15">
                            <button
                              type="button"
                              className="grid h-9 w-9 place-items-center"
                              aria-label="הפחתת כמות"
                              onClick={() => store.setQty(line.id, line.variantId, line.qty - 1)}
                            >
                              <IconMinus className="h-3.5 w-3.5" />
                            </button>
                            <span className="grid h-9 w-8 place-items-center text-sm tabular-nums">{line.qty}</span>
                            <button
                              type="button"
                              className="grid h-9 w-9 place-items-center"
                              aria-label="הגדלת כמות"
                              disabled={line.qty >= line.product.stock}
                              onClick={() => store.setQty(line.id, line.variantId, line.qty + 1)}
                            >
                              <IconPlus className="h-3.5 w-3.5" />
                            </button>
                          </div>
                          <span className="text-sm tabular-nums">{formatPrice(line.lineTotal)}</span>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <footer className="border-t border-white/10 px-5 py-4">
              <ShippingProgress
                subtotal={store.subtotal}
                remaining={store.remaining}
                progress={store.progress}
                freeReason={store.freeShippingReason}
              />
              {store.lines.length > 0 && (
                <CouponField
                  draft={couponDraft}
                  setDraft={setCouponDraft}
                  applied={store.appliedCoupon}
                  error={store.couponError}
                  eligible={store.firstOrderEligible}
                  onApply={() => {
                    if (store.applyCoupon(couponDraft || FIRST_ORDER_COUPON.code)) setCouponDraft("");
                  }}
                  onClear={() => {
                    store.clearCoupon();
                    setCouponDraft("");
                  }}
                />
              )}
              <Totals
                subtotal={store.subtotal}
                shipping={store.shipping}
                discount={store.discount}
                coupon={store.appliedCoupon}
                total={store.total}
                empty={store.lines.length === 0}
              />
              {store.lines.length === 0 ? (
                <button type="button" className="btn-gold mt-4 h-12 w-full" disabled>
                  המשך לפרטי משלוח
                </button>
              ) : (
                <button
                  type="button"
                  className="btn-gold mt-4 h-12 w-full"
                  onClick={() => store.setCheckoutStep("details")}
                >
                  המשך לפרטי משלוח · {formatPrice(store.total)}
                </button>
              )}
              {store.lines.length > 0 && <PurchaseTrust className="mt-3" />}
              <p className="mt-3 text-center text-[11px] text-muted">
                {store.freeShippingReason === "coupon"
                  ? "עם קופון הפתיחה — משלוח חינם עד הבית"
                  : "הסכום כולל משלוח במידת הצורך"}
                {" · "}
                התשלום בביט או PayPal אחרי אישור ההזמנה
              </p>
            </footer>
          </>
        )}
      </div>
    </Drawer>
  );
}

function PaymentOption({ selected, onSelect, title, subtitle, mark, accent = "gold" }) {
  const selectedClass =
    accent === "paypal"
      ? "border-[#0070ba]/80 bg-[#0070ba]/15 text-ivory shadow-[inset_0_0_0_1px_rgba(0,112,186,0.35)]"
      : "border-gold/70 bg-gold/10 text-ivory";
  return (
    <button
      type="button"
      role="radio"
      aria-checked={selected}
      onClick={onSelect}
      className={`flex flex-col items-start gap-2 border px-3 py-3 text-start transition ${
        selected ? selectedClass : "border-white/12 bg-black/20 text-muted hover:border-white/25 hover:text-ivory"
      }`}
    >
      <span className="flex w-full items-center justify-between gap-2">
        <span className="text-sm font-semibold text-ivory">{title}</span>
        {mark}
      </span>
      <span className="text-[11px] leading-4">{subtitle}</span>
    </button>
  );
}

function BitMark() {
  return (
    <span className="grid h-5 min-w-8 place-items-center rounded-full bg-white px-1.5 text-[10px] font-semibold text-black" dir="ltr">
      bit
    </span>
  );
}

function PayPalMark({ className = "h-4 w-auto" }) {
  return (
    <svg viewBox="0 0 80 24" className={className} aria-hidden="true">
      <text
        x="0"
        y="17"
        fill="currentColor"
        fontFamily="Helvetica, Arial, sans-serif"
        fontWeight="700"
        fontSize="16"
        letterSpacing="-0.4"
      >
        PayPal
      </text>
    </svg>
  );
}

function ShippingProgress({ subtotal, remaining, progress, freeReason = null }) {
  const qualified = remaining === 0 && subtotal > 0;
  const label =
    freeReason === "coupon"
      ? "משלוח חינם עם קופון הפתיחה"
      : `משלוח חינם מעל ${formatPrice(FREE_SHIPPING)}`;
  const status =
    subtotal === 0
      ? "התחילו להוסיף"
      : freeReason === "coupon"
        ? "המשלוח עלינו (קופון)"
        : qualified
          ? "המשלוח עלינו"
          : `עוד ${formatPrice(remaining)}`;
  return (
    <div className="mb-4">
      <div className="mb-2 flex items-center justify-between gap-3 text-xs">
        <span className="text-muted">{label}</span>
        <span className={qualified ? "text-gold-soft" : "text-ivory"}>{status}</span>
      </div>
      <div
        className="h-1.5 bg-white/10"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(progress)}
        aria-label="התקדמות למשלוח חינם"
      >
        <div className="h-full bg-gold transition-[width] duration-500" style={{ width: `${progress}%` }} />
      </div>
    </div>
  );
}

function CouponField({ draft, setDraft, applied, error, eligible, onApply, onClear }) {
  if (applied) {
    return (
      <div className="mb-3 flex items-center justify-between gap-3 border border-dashed border-gold/40 bg-gold/5 px-3 py-2.5 text-sm">
        <p>
          <span className="text-muted">קופון </span>
          <span className="font-semibold tracking-wide text-gold-soft" dir="ltr">
            {applied}
          </span>
          <span className="text-gold-soft"> · −{formatPrice(FIRST_ORDER_COUPON.amount)}</span>
        </p>
        <button type="button" className="text-xs text-muted underline-offset-2 hover:text-ivory hover:underline" onClick={onClear}>
          הסרה
        </button>
      </div>
    );
  }

  return (
    <div className="mb-3">
      <div className="flex gap-2">
        <input
          className="field h-10 flex-1 text-sm tracking-wide"
          dir="ltr"
          placeholder={eligible ? FIRST_ORDER_COUPON.code : "קוד קופון"}
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              onApply();
            }
          }}
          aria-label="קוד קופון"
        />
        <button type="button" className="btn-ghost h-10 shrink-0 px-4 text-sm" onClick={onApply}>
          מימוש
        </button>
      </div>
      {error ? (
        <p className="mt-1.5 text-xs text-[#e7b2a4]">{error}</p>
      ) : (
        <p className="mt-1.5 text-[11px] text-muted">
          {eligible
            ? `${FIRST_ORDER_COUPON.label} · הזינו ${FIRST_ORDER_COUPON.code}`
            : "קופון הזמנה ראשונה כבר נוצל במכשיר זה"}
        </p>
      )}
    </div>
  );
}

function Totals({ subtotal, shipping, discount = 0, coupon = "", total, empty = false }) {
  const free = !empty && shipping === 0;
  return (
    <div className="space-y-2 text-sm">
      <Row label="סיכום ביניים" value={formatPrice(subtotal)} />
      {!empty && discount > 0 && (
        <Row
          label={coupon ? `הנחה (${coupon})` : "הנחה"}
          value={`−${formatPrice(discount)}`}
          gold
        />
      )}
      <Row label="משלוח" value={empty ? "—" : free ? "חינם" : formatPrice(shipping)} gold={free} />
      <Row label="לתשלום" value={formatPrice(total)} strong />
    </div>
  );
}

function Row({ label, value, strong = false, gold = false }) {
  return (
    <p className={`flex items-center justify-between ${strong ? "border-t border-white/10 pt-2 text-base" : ""}`}>
      <span className="text-muted">{label}</span>
      <span className={`tabular-nums ${gold ? "text-gold-soft" : ""} ${strong ? "font-medium" : ""}`}>{value}</span>
    </p>
  );
}

function Field({ label, error, children }) {
  return (
    <label className="mb-3 block text-sm">
      <span className="mb-1.5 block text-muted">{label}</span>
      {children}
      {error && <span className="mt-1 block text-xs text-[#e7b2a4]">{error}</span>}
    </label>
  );
}
