import { useEffect, useState } from "react";
import { pages } from "../data";
import { useStore } from "../store";
import { IconClose } from "./Icons";

export default function InfoDialog() {
  const { info, closeInfo } = useStore();
  const page = info ? pages[info] : null;
  const [orderNumber, setOrderNumber] = useState("");
  const [phone, setPhone] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => {
    if (info !== "tracking") return;
    setOrderNumber("");
    setPhone("");
    setResult(null);
    setLoading(false);
  }, [info]);

  if (!page) return null;

  const track = async (event) => {
    event.preventDefault();
    const number = orderNumber.trim().toUpperCase();
    const phoneDigits = phone.replace(/[^\d]/g, "");
    if (!number && phoneDigits.length < 9) {
      setResult({
        ok: false,
        text: "הזינו מספר הזמנה (BRB-…) או מספר טלפון של ההזמנה.",
      });
      return;
    }

    setLoading(true);
    setResult(null);
    try {
      const res = await fetch("/api/track-order", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          orderNumber: number || undefined,
          phone: phone.trim() || undefined,
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || !data?.ok || !data.order) {
        const missingScript = data?.hint?.includes?.("Apps Script");
        setResult({
          ok: false,
          text: missingScript
            ? "מעקב ההזמנות מתעדכן כרגע. נסו שוב בעוד רגע, או פנו אלינו בוואטסאפ."
            : "לא מצאנו הזמנה תואמת. בדקו את מספר ההזמנה או הטלפון, או פנו אלינו בוואטסאפ.",
        });
        return;
      }
      setResult({ ok: true, order: data.order });
    } catch {
      setResult({
        ok: false,
        text: "לא הצלחנו לבדוק כרגע. נסו שוב בעוד רגע, או פנו אלינו בוואטסאפ.",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[70] flex items-end justify-center sm:items-center sm:p-6">
      <button type="button" className="absolute inset-0 bg-black/75 backdrop-blur-sm" aria-label="סגירה" onClick={closeInfo} />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="info-title"
        className="relative z-10 max-h-[88svh] w-full max-w-xl overflow-y-auto border border-line bg-[#0e0e10] p-6 sm:p-8"
      >
        <div className="flex items-start justify-between gap-4">
          <h2 id="info-title" className="font-display text-3xl leading-tight sm:text-4xl">
            {page.title}
          </h2>
          <button type="button" className="icon-btn" aria-label="סגירה" onClick={closeInfo}>
            <IconClose />
          </button>
        </div>
        <div className="mt-6 space-y-4 text-sm leading-7 text-ivory/80">
          {page.paragraphs.map((paragraph) => (
            <p key={paragraph}>{paragraph}</p>
          ))}
        </div>
        {info === "tracking" && (
          <form className="mt-6 space-y-3" onSubmit={track}>
            <label className="block text-sm">
              <span className="mb-1.5 block text-muted">מספר הזמנה</span>
              <input
                className="field"
                dir="ltr"
                value={orderNumber}
                placeholder="BRB-000000"
                autoComplete="off"
                onChange={(event) => setOrderNumber(event.target.value)}
              />
            </label>
            <label className="block text-sm">
              <span className="mb-1.5 block text-muted">או מספר טלפון מההזמנה</span>
              <input
                className="field"
                dir="ltr"
                inputMode="tel"
                value={phone}
                placeholder="05XXXXXXXX"
                autoComplete="tel"
                onChange={(event) => setPhone(event.target.value)}
              />
            </label>
            <button type="submit" className="btn-gold h-11 px-5 text-sm" disabled={loading}>
              {loading ? "בודקים…" : "בדיקת סטטוס"}
            </button>

            {result && !result.ok && (
              <p className="text-sm leading-7 text-[#e7b2a4]" role="status">
                {result.text}
              </p>
            )}

            {result?.ok && result.order ? <TrackResult order={result.order} /> : null}
          </form>
        )}
      </div>
    </div>
  );
}

function TrackResult({ order }) {
  return (
    <div className="mt-2 space-y-4 border border-white/10 bg-black/30 px-4 py-4" role="status">
      <div>
        <p className="text-xs tracking-wide text-muted">מספר הזמנה</p>
        <p className="mt-1 text-base font-semibold tracking-wide text-ivory" dir="ltr">
          {order.number}
        </p>
      </div>

      <div>
        <p className="text-base font-medium text-gold-soft">{order.headline}</p>
        <p className="mt-1 text-sm leading-7 text-ivory/80">{order.detail}</p>
      </div>

      {order.timeline?.length ? (
        <ol className="space-y-2 border-t border-white/10 pt-4">
          {order.timeline.map((step) => (
            <li key={step.id} className="flex items-center gap-3 text-sm">
              <span
                className={`inline-flex h-2.5 w-2.5 shrink-0 rounded-full ${
                  step.state === "done"
                    ? "bg-gold"
                    : step.state === "current"
                      ? "bg-gold-soft ring-2 ring-gold/40"
                      : "bg-white/20"
                }`}
                aria-hidden="true"
              />
              <span
                className={
                  step.state === "todo" ? "text-muted" : step.state === "current" ? "text-ivory" : "text-ivory/80"
                }
              >
                {step.label}
              </span>
            </li>
          ))}
        </ol>
      ) : null}

      <div className="space-y-1 border-t border-white/10 pt-3 text-xs leading-6 text-muted">
        {order.city ? <p>יעד: {order.city}</p> : null}
        {order.items ? <p>פריטים: {order.items}</p> : null}
        {order.createdAt ? <p>תאריך הזמנה: {order.createdAt}</p> : null}
        {order.shipDays != null ? <p>ימים בדרך: {order.shipDays}</p> : null}
      </div>
    </div>
  );
}
