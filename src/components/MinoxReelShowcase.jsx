import { useCallback, useEffect, useRef, useState } from "react";

const SHOP_URL = "https://www.minox-shop.co.il";
const BEAT_MS = 3200;

const BEATS = [
  {
    id: "hook",
    image: "/minox-reel/01-hook.jpg",
    eyebrow: "MinoxShop · הנמכר ביותר",
    title: (
      <>
        רוגיין <mark className="reel-mark">מקורי</mark> מארה״ב
      </>
    ),
    sub: "קצף לגברים · מארז כפול ל־6 חודשים",
    badges: ["100% מקורי מארה״ב"],
  },
  {
    id: "value",
    image: "/minox-reel/02-value.jpg",
    eyebrow: "קצף שנספג מהר",
    title: (
      <>
        טיפול <mark className="reel-mark">מהיר</mark> ונוח לשימוש
      </>
    ),
    sub: "פעמיים ביום · בלי ריח חזק",
    badges: ["100% מקורי מארה״ב"],
  },
  {
    id: "offer",
    image: "/minox-reel/03-offer.jpg",
    eyebrow: "מבצע נובמבר",
    title: (
      <>
        10% נקודות בונוס · משלוח <mark className="reel-mark">חינם</mark>
      </>
    ),
    sub: "צוברים נקודות על כל קנייה",
    badges: ["100% מקורי מארה״ב", "משלוח חינם עד הבית"],
  },
  {
    id: "cta",
    image: "/minox-reel/04-cta.jpg",
    eyebrow: "מוכנים להתחיל?",
    title: (
      <>
        לרכישה באתר — משלוח <mark className="reel-mark">חינם</mark> עד הבית
      </>
    ),
    sub: "minox-shop.co.il",
    badges: ["משלוח חינם עד הבית"],
    cta: true,
  },
];

export default function MinoxReelShowcase() {
  const [beat, setBeat] = useState(0);
  const [paused, setPaused] = useState(false);
  const touchX = useRef(null);
  const reduceMotion = useRef(false);

  useEffect(() => {
    reduceMotion.current = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }, []);

  useEffect(() => {
    if (paused || reduceMotion.current) return undefined;
    const id = window.setTimeout(() => {
      setBeat((b) => (b + 1) % BEATS.length);
    }, BEAT_MS);
    return () => window.clearTimeout(id);
  }, [beat, paused]);

  const go = useCallback((next) => {
    setBeat((next + BEATS.length) % BEATS.length);
  }, []);

  const onPointerDown = (e) => {
    touchX.current = e.clientX ?? e.touches?.[0]?.clientX ?? null;
  };

  const onPointerUp = (e) => {
    const start = touchX.current;
    touchX.current = null;
    if (start == null) return;
    const end = e.clientX ?? e.changedTouches?.[0]?.clientX ?? start;
    const dx = end - start;
    if (Math.abs(dx) > 40) {
      // RTL: swipe left = next
      go(beat + (dx < 0 ? 1 : -1));
      return;
    }
    // tap zones: right third = prev (RTL), left third = next
    const w = e.currentTarget?.clientWidth || window.innerWidth;
    const x = end;
    if (x < w * 0.33) go(beat + 1);
    else if (x > w * 0.66) go(beat - 1);
  };

  const current = BEATS[beat];

  return (
    <div className="reel-page" dir="rtl" lang="he">
      <div className="reel-shell">
        <header className="reel-topbar">
          <p className="reel-brand">MinoxShop</p>
          <a className="reel-top-link" href={SHOP_URL} target="_blank" rel="noopener noreferrer">
            לאתר
          </a>
        </header>

        <div
          className="reel-stage"
          onMouseDown={onPointerDown}
          onMouseUp={onPointerUp}
          onTouchStart={onPointerDown}
          onTouchEnd={onPointerUp}
          role="region"
          aria-label="ריל מוצרים של MinoxShop"
        >
          <div className="reel-progress" aria-hidden="true">
            {BEATS.map((b, i) => (
              <span key={b.id} className={`reel-progress-seg ${i === beat ? "is-active" : i < beat ? "is-done" : ""}`} />
            ))}
          </div>

          <img
            key={current.id}
            src={current.image}
            alt=""
            className="reel-frame reel-in"
            draggable={false}
          />

          <div className="reel-scrim" aria-hidden="true" />

          <div key={`${current.id}-copy`} className="reel-copy">
            <div className="reel-badges reel-in">
              {current.badges.map((badge) => (
                <span key={badge} className="reel-badge">
                  {badge}
                </span>
              ))}
            </div>
            <p className="reel-eyebrow reel-in reel-in-2">{current.eyebrow}</p>
            <h1 className="reel-title reel-in reel-in-2">{current.title}</h1>
            <p className="reel-sub reel-in reel-in-3">{current.sub}</p>

            {current.cta ? (
              <a
                className="reel-cta reel-in reel-in-3"
                href={SHOP_URL}
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => e.stopPropagation()}
              >
                קחו אותי לחנות
              </a>
            ) : null}
          </div>

          <button
            type="button"
            className="reel-pause"
            aria-label={paused ? "המשך" : "השהה"}
            onClick={(e) => {
              e.stopPropagation();
              setPaused((p) => !p);
            }}
          >
            {paused ? "▶" : "❚❚"}
          </button>
        </div>

        <nav className="reel-dots" aria-label="בחירת פריים">
          {BEATS.map((b, i) => (
            <button
              key={b.id}
              type="button"
              className={`reel-dot ${i === beat ? "is-active" : ""}`}
              aria-label={`פריים ${i + 1}`}
              aria-current={i === beat ? "true" : undefined}
              onClick={() => go(i)}
            />
          ))}
        </nav>

        <p className="reel-hint">החליקו או לחצו למעבר בין הפריימים</p>
      </div>
    </div>
  );
}
