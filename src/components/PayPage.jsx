import { useEffect, useState } from "react";
import { formatPrice } from "../data";
import { trackMetaAddPaymentInfo } from "../metaPixel";
import { openPayPalPayment } from "../payment";
import BitPayPanel from "./BitPayPanel";
import { Logo } from "./Header";
import { PayPalMark } from "./PaymentMarks";

export default function PayPage() {
  const [state, setState] = useState({ status: "loading", order: null, error: "" });

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
  const isPayBox = order?.payment === "paybox";

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
              <p className="mt-6 text-center text-xs text-muted">
                מספר הזמנה{" "}
                <span className="font-semibold tracking-wide text-ivory" dir="ltr">
                  {order.number}
                </span>
              </p>

              <div className="mt-5">
                {isPaypal ? (
                  <div>
                    <div className="border border-white/10 bg-black/40 px-4 py-5 text-center">
                      <p className="text-xs tracking-wide text-muted">לתשלום ב-PayPal</p>
                      <p className="mt-2 font-display text-5xl leading-none text-gold-soft tabular-nums" dir="ltr">
                        {formatPrice(order.total)}
                      </p>
                    </div>
                    <button
                      type="button"
                      className="mt-6 inline-flex h-14 w-full items-center justify-center gap-2 bg-[#0070ba] text-base font-semibold text-white transition hover:bg-[#005ea6]"
                      onClick={() => {
                        trackMetaAddPaymentInfo(order);
                        openPayPalPayment(order);
                      }}
                    >
                      <PayPalMark className="h-4 w-auto brightness-0 invert" />
                      שלם עכשיו ב-PayPal
                    </button>
                  </div>
                ) : (
                  <BitPayPanel order={order} provider={isPayBox ? "paybox" : "bit"} />
                )}
              </div>
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
