/**
 * Bold limited-stock cue for flash / clearance SKUs.
 * Always uses the real stock count — no fake “last one” claims.
 */
export default function StockUrgency({ stock, className = "" }) {
  const n = Number(stock) || 0;
  if (n <= 0) return null;

  const critical = n <= 3;
  const almostGone = n <= 10;
  const label = critical
    ? n === 1
      ? "נותרה יחידה אחת במלאי"
      : `נותרו רק ${n} יחידות — עומד להיגמר`
    : almostGone
      ? `נשארו רק ${n} במלאי — עומד להיגמר`
      : `מלאי מוגבל · נשארו ${n}`;

  const tone = critical || almostGone ? "urgent" : "warn";

  return (
    <div
      className={`relative overflow-hidden border px-3.5 py-3 ${
        tone === "urgent"
          ? "border-[#c45c4a]/55 bg-[#c45c4a]/12"
          : "border-gold/45 bg-gold/10"
      } ${className}`}
      role="status"
    >
      <div
        className={`pointer-events-none absolute inset-y-0 start-0 w-1 ${
          tone === "urgent" ? "bg-[#e07a68]" : "bg-gold"
        }`}
        aria-hidden="true"
      />
      <p
        className={`text-[13px] font-semibold leading-5 tracking-wide sm:text-sm ${
          tone === "urgent" ? "text-[#f0b4a8]" : "text-gold-soft"
        }`}
      >
        {label}
      </p>
      <p className="mt-0.5 text-[11px] leading-4 text-ivory/60">
        {almostGone ? "מלאי אחרון במבצע · כדאי לסגור עכשיו" : "מבצע חיסול · כל עוד המלאי נמשך"}
      </p>
    </div>
  );
}
