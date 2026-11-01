/**
 * Bold limited-stock cue for flash / clearance SKUs.
 * Always uses the real stock count — no fake “last one” claims.
 */
export default function StockUrgency({ stock, className = "" }) {
  const n = Number(stock) || 0;
  if (n <= 0) return null;

  const almostGone = n <= 5;
  const label = almostGone
    ? n === 1
      ? "נותרה יחידה אחת במלאי"
      : `נותרו רק ${n} יחידות במלאי`
    : `מלאי מוגבל · נשארו ${n}`;

  return (
    <div
      className={`relative overflow-hidden border px-3.5 py-3 ${
        almostGone
          ? "border-[#c45c4a]/55 bg-[#c45c4a]/12"
          : "border-gold/45 bg-gold/10"
      } ${className}`}
      role="status"
    >
      <div
        className={`pointer-events-none absolute inset-y-0 start-0 w-1 ${
          almostGone ? "bg-[#e07a68]" : "bg-gold"
        }`}
        aria-hidden="true"
      />
      <p
        className={`text-[13px] font-semibold leading-5 tracking-wide sm:text-sm ${
          almostGone ? "text-[#f0b4a8]" : "text-gold-soft"
        }`}
      >
        {label}
      </p>
      <p className="mt-0.5 text-[11px] leading-4 text-ivory/60">
        {almostGone ? "כמעט אזל · כדאי לסגור עכשיו" : "מבצע חיסול · כל עוד המלאי נמשך"}
      </p>
    </div>
  );
}
