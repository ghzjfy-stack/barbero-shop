import { useState } from "react";
import { FREE_SHIPPING, formatPrice } from "../data";
import { useStore } from "../store";
import Drawer from "./Drawer";
import { IconClose, IconMinus, IconPlus, IconTrash } from "./Icons";
import ProductImage, { imageFrame } from "./ProductImage";

const BIT_PHONE = "0543554888";

function bitTransferUrl(amount) {
  const total = Number(amount);
  const value = Number.isFinite(total) && total > 0 ? total : 0;
  return `https://www.bitpay.co.il/app/transfer?phone=${BIT_PHONE}&amount=${value}`;
}

function prefersBitApp() {
  if (typeof navigator === "undefined") return false;
  const ua = navigator.userAgent.toLowerCase();
  if (/iphone|ipad|ipod|android/.test(ua)) return true;
  return navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1;
}

const emptyDetails = {
  name: "",
  phone: "",
  city: "",
  address: "",
  unit: "",
  postal: "",
  notes: "",
  agree: false,
};

export default function CartDrawer() {
  const store = useStore();
  const [details, setDetails] = useState(emptyDetails);
  const [errors, setErrors] = useState({});
  const [copied, setCopied] = useState(false);

  const setField = (key, value) => {
    setDetails((current) => ({ ...current, [key]: value }));
    setErrors((current) => ({ ...current, [key]: undefined }));
  };

  const validate = () => {
    const next = {};
    if (details.name.trim().length < 2) next.name = "נשמח לשם מלא";
    const phone = details.phone.replace(/[^\d]/g, "");
    if (phone.length < 9 || phone.length > 13) next.phone = "מספר טלפון לא תקין";
    if (details.city.trim().length < 2) next.city = "חסרה עיר";
    if (details.address.trim().length < 4) next.address = "חסרה כתובת למשלוח";
    const postal = details.postal.trim();
    if (postal && !/^\d{5}(\d{2})?$/.test(postal)) next.postal = "מיקוד לא תקין";
    if (!details.agree) next.agree = "יש לאשר את התקנון כדי להמשיך";
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const submit = (event) => {
    event.preventDefault();
    if (!validate()) return;
    store.placeOrder({
      name: details.name.trim(),
      phone: details.phone.trim(),
      city: details.city.trim(),
      address: details.address.trim(),
      unit: details.unit.trim(),
      postal: details.postal.trim(),
      notes: details.notes.trim(),
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

  const whatsappHref = store.order
    ? `https://wa.me/972543554888?text=${encodeURIComponent(`שלום, אישור תשלום עבור הזמנה ${store.order.number}`)}`
    : "https://wa.me/972543554888";
  const mobileBit = prefersBitApp();
  const bitLinkProps = mobileBit ? {} : { target: "_blank", rel: "noopener noreferrer" };

  return (
    <Drawer open={store.cartOpen} onClose={store.closeCart} label="עגלת קניות">
      <div id="cart-drawer" className="flex h-full flex-col">
        <header className="flex items-center justify-between border-b border-white/10 px-5 py-4">
          <div>
            <p className="text-[11px] text-gold">BARBERO</p>
            <h2 className="font-display text-3xl leading-none">
              {store.checkoutStep === "done" ? "ההזמנה התקבלה" : "העגלה"}
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
          <div className="flex flex-1 flex-col overflow-y-auto px-5 py-8">
            <p className="text-sm leading-7 text-ivory/75">תודה, {store.order.details.name}.</p>
            <p className="mt-5 border border-gold/50 bg-gold/10 px-4 py-4 text-base font-semibold leading-8 text-ivory">
              להשלמת ההזמנה, אנא העבר{" "}
              <span className="tabular-nums" dir="ltr">
                {formatPrice(store.order.total)}
              </span>{" "}
              ב-Bit למספר <span dir="ltr">054-3554888</span>
            </p>
            <p className="mt-6 text-xs text-muted">מספר הזמנה</p>
            <p className="mt-1 font-display text-4xl text-gold-soft" dir="ltr">
              {store.order.number}
            </p>
            <button type="button" className="btn-ghost mt-4 h-11" onClick={copyNumber}>
              {copied ? "המספר הועתק" : "העתקת מספר"}
            </button>
            <a
              className="mt-3 inline-flex h-12 w-full items-center justify-center bg-[#25D366] text-base font-semibold text-[#06281a] transition hover:bg-[#3ee07a]"
              href={whatsappHref}
              target="_blank"
              rel="noopener noreferrer"
            >
              שלח אישור תשלום בוואטסאפ
            </a>
            <p className="mt-5 text-center text-xs leading-6 text-muted">
              סרוק את קוד ה-QR לתשלום מהיר ב-Bit, או לחץ על הכפתור למטה
            </p>
            <img
              className="mx-auto mt-3 block max-w-[200px] rounded-lg"
              src="/bit-qr.jpg"
              alt="קוד QR לתשלום ב-Bit"
              width="200"
            />
            <a
              className="btn-ghost mt-4 h-12 w-full"
              href={bitTransferUrl(store.order.total)}
              {...bitLinkProps}
            >
              תשלום בביט
            </a>
            <ul className="mt-8 space-y-3 border-t border-white/10 pt-5 text-sm">
              {store.order.lines.map((line) => (
                <li key={`${line.name}-${line.label || ""}`} className="flex justify-between gap-4">
                  <span>
                    {line.name}
                    {line.label ? ` · ${line.label}` : ""} × {line.qty}
                  </span>
                  <span className="tabular-nums">{formatPrice(line.lineTotal)}</span>
                </li>
              ))}
            </ul>
            <div className="mt-4">
              <Totals subtotal={store.order.subtotal} shipping={store.order.shipping} total={store.order.total} />
            </div>
            <p className="mt-2 text-sm text-muted">
              {[store.order.details.address, store.order.details.unit, store.order.details.city, store.order.details.postal]
                .filter(Boolean)
                .join(", ")}
            </p>
            {store.order.details.notes && <p className="mt-2 text-sm leading-7 text-muted">{store.order.details.notes}</p>}
            <button type="button" className="btn-gold mt-auto h-12" onClick={store.finishCheckout}>
              המשך בקניות
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
            <p className="mt-4 text-xs leading-6 text-muted">התשלום מתבצע בביט בלבד. התשלום מאובטח בתקן SSL מחמיר.</p>
            <div className="mt-auto pt-6">
              <ShippingProgress subtotal={store.subtotal} remaining={store.remaining} progress={store.progress} />
              <Totals subtotal={store.subtotal} shipping={store.shipping} total={store.total} />
              <div className="mt-4 grid gap-2">
                <button type="submit" className="btn-gold h-12">
                  אישור הזמנה · {formatPrice(store.total)}
                </button>
                <button type="button" className="btn-ghost h-11" onClick={() => store.setCheckoutStep("cart")}>
                  חזרה לעגלה
                </button>
              </div>
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
                            <h3 className="text-sm leading-5">{line.product.name}</h3>
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
              <ShippingProgress subtotal={store.subtotal} remaining={store.remaining} progress={store.progress} />
              <Totals
                subtotal={store.subtotal}
                shipping={store.shipping}
                total={store.total}
                empty={store.lines.length === 0}
              />
              {store.lines.length === 0 ? (
                <button type="button" className="btn-gold mt-4 h-12 w-full" disabled>
                  תשלום בביט
                </button>
              ) : (
                <a
                  className="btn-gold mt-4 h-12 w-full"
                  href={bitTransferUrl(store.total)}
                  {...bitLinkProps}
                  onClick={() => store.setCheckoutStep("details")}
                >
                  תשלום בביט
                </a>
              )}
              <p className="mt-3 text-center text-[11px] text-muted">מקבלים ביט בלבד · יבוא מקורי · אחריות רשמית</p>
            </footer>
          </>
        )}
      </div>
    </Drawer>
  );
}

function ShippingProgress({ subtotal, remaining, progress }) {
  const qualified = remaining === 0 && subtotal > 0;
  return (
    <div className="mb-4">
      <div className="mb-2 flex items-center justify-between gap-3 text-xs">
        <span className="text-muted">משלוח חינם מעל {formatPrice(FREE_SHIPPING)}</span>
        <span className={qualified ? "text-gold-soft" : "text-ivory"}>
          {subtotal === 0 ? "התחילו להוסיף" : qualified ? "המשלוח עלינו" : `עוד ${formatPrice(remaining)}`}
        </span>
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

function Totals({ subtotal, shipping, total, empty = false }) {
  const free = !empty && shipping === 0;
  return (
    <div className="space-y-2 text-sm">
      <Row label="סיכום ביניים" value={formatPrice(subtotal)} />
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
