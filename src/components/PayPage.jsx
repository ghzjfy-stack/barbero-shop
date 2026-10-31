import { useEffect, useState } from "react";
import { formatPrice } from "../data";
import { trackMetaAddPaymentInfo, trackMetaPurchaseOnce } from "../metaPixel";
import { BIT_PERSONAL_URL, openPayPalPayment } from "../payment";
import { Logo } from "./Header";

function PayPalMark({ className = "h-4 w-auto" }) {
  return (
    <svg className={className} viewBox="0 0 100 32" aria-hidden="true">
      <path
        fill="currentColor"
        d="M12 3h18.2c5.7 0 9.7 3 9.7 8.1 0 6.6-4.5 11.3-11.1 11.3H22l-1.7 9.1H12.4L16.3 3zm7.4 6.2l-1.5 8h5.2c3.1 0 5.1-1.7 5.1-4.3 0-2.1-1.4-3.7-4.2-3.7H19.4zM58.6 3h7.8l-4.7 25.5h-7.8L58.6 3zm-14.2 0h7.5l-1.2 6.6h7c5.4 0 9 3.1 7.8 8.7C63.8 25 59.2 28.5 53 28.5h-9.8L48.4 3h-4zm1.7 6.2l-1.9 10.4h4.6c2.9 0 5.1-1.5 5.7-4.5.6-2.8-.9-4.5-3.8-4.5h-4.6zM84.4 9.2h-7.1L75.8 16c-.2 1.1.3 1.7 1.4 1.7h2.1l-.8 4.5c-3.7 1.7-7.2 2.4-10.1 2.4-5.7 0-9.6-3.5-8.4-9.4C61.4 8.3 67.3 3 75.2 3c2.6 0 5.2.5 7.8 1.4l-1.5 7.8c-1.7-.8-3.3-1.2-4.7-1.2-3.3 0-5.6 1.9-6.2 4.8-.5 2.6.8 4.2 3.4 4.2 1.4 0 2.9-.4 4.5-1.1l.4-2.3h-4.1l.7-3.8h11.2l-1.3 7.4z"
      />
    </svg>
  );
}

export default function PayPage() {
  const [state, setState] = useState({ status: "loading", order: null, error: "" });
  const [amountCopied, setAmountCopied] = useState(false);
  const [paidMarked, setPaidMarked] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const o = params.get("o") || "";
    const t = params.get("t") || "";
    const p = params.get("p") || "";
    const k = params.get("k") || "";
    if (!o || !t || !k) {
      setState({ status: "error", order: null, error: "קישור התשלום אינו תקין או חסר." });
      return;
    }

    const qs = new URLSearchParams({ o, t, p, k });
    fetch(`/api/pay-info?${qs.toString()}`)
      .then(async (res) => {
        const data = await res.json().catch(() => ({}));
        if (!res.ok || !data?.ok || !data.order) {
          throw new Error(data?.error || "invalid_link");
        }
        setState({ status: "ready", order: data.order, error: "" });
      })
      .catch(() => {
        setState({
          status: "error",
          order: null,
          error: "לא הצלחנו לאמת את קישור התשלום. נסו שוב מהמייל, או פנו אלינו בוואטסאפ.",
        });
      });
  }, []);

  const order = state.order;
  const isPaypal = order?.payment === "paypal";

  const copyAmount = async () => {
    if (!order) return;
    try {
      await navigator.clipboard.writeText(String(Number(order.total) || 0));
      setAmountCopied(true);
      window.setTimeout(() => setAmountCopied(false), 1800);
    } catch {
      setAmountCopied(false);
    }
  };

  const confirmPaid = () => {
    if (!order) return;
    trackMetaPurchaseOnce(order);
    setPaidMarked(true);
  };

  return (
    <section className="relative min-h-[100svh] overflow-hidden px-4 pb-16 pt-28 sm:px-6 lg:px-8">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_20%_0%,rgba(198,161,91,0.16),transparent_42%),linear-gradient(160deg,#141210,#090909)]" />
      <div className="relative mx-auto w-full max-w-md">
        <div className="mb-8 flex justify-center">
          <Logo />
        </div>

        <div className="border border-white/10 bg-black/35 px-5 py-7 backdrop-blur-sm sm:px-7">
          <p className="text-center text-[11px] tracking-[0.18em] text-gold">תשלום הזמנה</p>
          <h1 className="mt-3 text-center font-display text-3xl leading-none">להשלמת הרכישה</h1>

          {state.status === "loading" ? (
            <p className="mt-8 text-center text-sm text-muted">טוען פרטי תשלום…</p>
          ) : null}

          {state.status === "error" ? (
            <p className="mt-8 text-center text-sm leading-7 text-ivory/80">{state.error}</p>
          ) : null}

          {state.status === "ready" && order ? (
            <>
              <div className="mt-8 border border-white/10 bg-black/40 px-4 py-5 text-center">
                <p className="text-xs text-muted">מספר הזמנה</p>
                <p className="mt-1 text-lg font-semibold tracking-wide text-ivory" dir="ltr">
                  {order.number}
                </p>
                <p className="mt-5 text-xs tracking-wide text-muted">
                  {isPaypal ? "לתשלום ב-PayPal" : "לתשלום בביט"}
                </p>
                <p className="mt-2 font-display text-5xl leading-none text-gold-soft tabular-nums" dir="ltr">
                  {formatPrice(order.total)}
                </p>
                {!isPaypal ? (
                  <button
                    type="button"
                    className="mt-3 text-xs text-gold-soft underline-offset-2 hover:underline"
                    onClick={copyAmount}
                  >
                    {amountCopied ? "הסכום הועתק" : "העתיקו את הסכום לביט"}
                  </button>
                ) : null}
              </div>

              <div className="mt-6">
                {isPaypal ? (
                  <button
                    type="button"
                    className="inline-flex h-14 w-full items-center justify-center gap-2 bg-[#0070ba] text-base font-semibold text-white transition hover:bg-[#005ea6]"
                    onClick={() => {
                      trackMetaAddPaymentInfo(order);
                      openPayPalPayment(order);
                    }}
                  >
                    <PayPalMark className="h-4 w-auto brightness-0 invert" />
                    שלם עכשיו ב-PayPal
                  </button>
                ) : (
                  <a
                    className="btn-gold inline-flex h-14 w-full items-center justify-center text-base"
                    href={BIT_PERSONAL_URL}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={() => trackMetaAddPaymentInfo(order)}
                  >
                    שלם עכשיו בביט
                  </a>
                )}
              </div>

              {!isPaypal ? (
                <p className="mt-3 text-center text-[11px] leading-5 text-muted">
                  בביט הזינו ידנית {formatPrice(order.total)} וציינו את מספר ההזמנה.
                </p>
              ) : null}

              <button
                type="button"
                className={`mt-4 h-11 w-full border text-sm transition ${
                  paidMarked
                    ? "border-gold/50 bg-gold/10 text-gold-soft"
                    : "border-white/15 text-ivory hover:border-gold/40"
                }`}
                onClick={confirmPaid}
                disabled={paidMarked}
              >
                {paidMarked ? "תודה — קיבלנו אישור תשלום" : "אישרתי ששילמתי"}
              </button>

              <p className="mt-5 text-center text-xs leading-6 text-muted">
                אחרי התשלום אנחנו מקבלים התראה וממשיכים לטיפול בהזמנה.
              </p>
            </>
          ) : null}
        </div>

        <p className="mt-6 text-center text-sm text-muted">
          צריכים עזרה?{" "}
          <a className="text-gold-soft hover:underline" href="https://wa.me/972543554888">
            וואטסאפ
          </a>
        </p>
      </div>
    </section>
  );
}
