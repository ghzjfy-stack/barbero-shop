import { useState } from "react";
import { FREE_SHIPPING, formatPrice } from "../data";
import { useStore } from "../store";
import Drawer from "./Drawer";
import { IconClose, IconMinus, IconPlus, IconTrash } from "./Icons";
import ProductImage from "./ProductImage";

const emptyDetails = { name: "", phone: "", city: "", address: "", agree: false };

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
          <div className="flex flex-1 flex-col px-5 py-8">
            <p className="text-sm leading-7 text-ivory/75">
              תודה, {store.order.details.name}. שמרנו את ההזמנה במכשיר הזה. אין כאן חיוב ואין משלוח אמיתי.
            </p>
            <p className="mt-6 text-xs text-muted">מספר הזמנה</p>
            <p className="mt-1 font-display text-4xl text-gold-soft" dir="ltr">
              {store.order.number}
            </p>
            <button type="button" className="btn-ghost mt-4 h-11" onClick={copyNumber}>
              {copied ? "המספר הועתק" : "העתקת מספר"}
            </button>
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
            <p className="mt-4 flex justify-between border-t border-white/10 pt-4 text-base">
              <span>לתשלום</span>
              <span className="tabular-nums">{formatPrice(store.order.total)}</span>
            </p>
            <p className="mt-2 text-sm text-muted">
              {store.order.details.address}, {store.order.details.city}
            </p>
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
              התשלום מתבצע בביט בלבד. ההזמנה נשמרת במכשיר זה בלבד ואינה נשלחת לסליקה.
            </p>
            <div className="mt-auto grid gap-2 pt-6">
              <button type="submit" className="btn-gold h-12">
                אישור הזמנה · {formatPrice(store.total)}
              </button>
              <button type="button" className="btn-ghost h-11" onClick={() => store.setCheckoutStep("cart")}>
                חזרה לעגלה
              </button>
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
                      <div className="h-24 overflow-hidden bg-[#1a1814]">
                        <ProductImage src={line.product.image} alt="" className="h-full w-full object-cover" />
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
              <div className="mb-4">
                <div className="mb-2 flex items-center justify-between text-xs">
                  <span className="text-muted">משלוח חינם מעל {formatPrice(FREE_SHIPPING)}</span>
                  <span className={store.remaining === 0 && store.subtotal > 0 ? "text-gold-soft" : "text-ivory"}>
                    {store.subtotal === 0
                      ? "התחילו להוסיף"
                      : store.remaining === 0
                        ? "המשלוח עלינו"
                        : `עוד ${formatPrice(store.remaining)}`}
                  </span>
                </div>
                <div
                  className="h-1.5 bg-white/10"
                  role="progressbar"
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-valuenow={Math.round(store.progress)}
                  aria-label="התקדמות למשלוח חינם"
                >
                  <div className="h-full bg-gold transition-[width] duration-500" style={{ width: `${store.progress}%` }} />
                </div>
              </div>

              <div className="space-y-2 text-sm">
                <Row label="סיכום ביניים" value={formatPrice(store.subtotal)} />
                <Row
                  label="משלוח"
                  value={store.lines.length === 0 ? "—" : store.shipping === 0 ? "חינם" : formatPrice(store.shipping)}
                  gold={store.lines.length > 0 && store.shipping === 0}
                />
                <Row label="לתשלום" value={formatPrice(store.total)} strong />
              </div>
              <button
                type="button"
                className="btn-gold mt-4 h-12 w-full"
                disabled={store.lines.length === 0}
                onClick={() => store.setCheckoutStep("details")}
              >
                תשלום בביט
              </button>
              <p className="mt-3 text-center text-[11px] text-muted">מקבלים ביט בלבד · יבוא מקורי · אחריות רשמית</p>
            </footer>
          </>
        )}
      </div>
    </Drawer>
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
