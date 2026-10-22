import { useState } from "react";
import { pages } from "../data";
import { useStore } from "../store";
import { IconClose } from "./Icons";

export default function InfoDialog() {
  const { info, closeInfo, lastOrder } = useStore();
  const page = info ? pages[info] : null;
  const [orderNumber, setOrderNumber] = useState("");
  const [result, setResult] = useState(null);

  if (!page) return null;

  const track = (event) => {
    event.preventDefault();
    const value = orderNumber.trim().toUpperCase();
    if (!value) {
      setResult({ ok: false, text: "הזינו מספר הזמנה." });
      return;
    }
    if (lastOrder && value === lastOrder.number.toUpperCase()) {
      setResult({
        ok: true,
        text: `ההזמנה ${lastOrder.number} אושרה ונארזת. היעד: ${lastOrder.details.city}.`,
      });
      return;
    }
    setResult({ ok: false, text: "לא מצאנו הזמנה עם המספר הזה. בדקו את האישור שקיבלתם." });
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
                onChange={(event) => setOrderNumber(event.target.value)}
              />
            </label>
            <button type="submit" className="btn-gold h-11 px-5 text-sm">
              בדיקת סטטוס
            </button>
            {result && (
              <p className={`text-sm leading-7 ${result.ok ? "text-gold-soft" : "text-[#e7b2a4]"}`} role="status">
                {result.text}
              </p>
            )}
          </form>
        )}
      </div>
    </div>
  );
}
