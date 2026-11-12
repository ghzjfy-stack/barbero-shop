const SHOP_URL = "https://www.minox-shop.co.il";
const BEAT_MS = 3200;

const BEATS = [
  {
    id: "hook",
    image: "./frames/01-hook.jpg",
    eyebrow: "MinoxShop · הנמכר ביותר",
    titleHtml: 'רוגיין <mark class="reel-mark">מקורי</mark> מארה״ב',
    sub: "קצף לגברים · מארז כפול ל־6 חודשים",
    badges: ["100% מקורי מארה״ב"],
  },
  {
    id: "value",
    image: "./frames/02-value.jpg",
    eyebrow: "קצף שנספג מהר",
    titleHtml: 'טיפול <mark class="reel-mark">מהיר</mark> ונוח לשימוש',
    sub: "פעמיים ביום · בלי ריח חזק",
    badges: ["100% מקורי מארה״ב"],
  },
  {
    id: "offer",
    image: "./frames/03-offer.jpg",
    eyebrow: "מבצע נובמבר",
    titleHtml: '10% נקודות בונוס · משלוח <mark class="reel-mark">חינם</mark>',
    sub: "צוברים נקודות על כל קנייה",
    badges: ["100% מקורי מארה״ב", "משלוח חינם עד הבית"],
  },
  {
    id: "cta",
    image: "./frames/04-cta.jpg",
    eyebrow: "מוכנים להתחיל?",
    titleHtml: 'לרכישה באתר — משלוח <mark class="reel-mark">חינם</mark> עד הבית',
    sub: "minox-shop.co.il",
    badges: ["משלוח חינם עד הבית"],
    cta: true,
  },
];

const stage = document.getElementById("stage");
const frame = document.getElementById("frame");
const copy = document.getElementById("copy");
const progress = document.getElementById("progress");
const dots = document.getElementById("dots");
const pauseBtn = document.getElementById("pause");

let beat = 0;
let paused = false;
let timer = null;
let touchX = null;
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

progress.innerHTML = BEATS.map(() => '<span class="reel-progress-seg"></span>').join("");
dots.innerHTML = BEATS.map(
  (_, i) => `<button type="button" class="reel-dot" aria-label="פריים ${i + 1}" data-i="${i}"></button>`
).join("");

function go(next) {
  beat = (next + BEATS.length) % BEATS.length;
  render();
}

function schedule() {
  window.clearTimeout(timer);
  if (paused || reduceMotion) return;
  timer = window.setTimeout(() => go(beat + 1), BEAT_MS);
}

function render() {
  const current = BEATS[beat];
  frame.src = current.image;
  frame.className = "reel-frame reel-in";

  const badges = current.badges.map((b) => `<span class="reel-badge">${b}</span>`).join("");
  const cta = current.cta
    ? `<a class="reel-cta reel-in reel-in-3" href="${SHOP_URL}" target="_blank" rel="noopener noreferrer">קחו אותי לחנות</a>`
    : "";

  copy.innerHTML = `
    <div class="reel-badges reel-in">${badges}</div>
    <p class="reel-eyebrow reel-in reel-in-2">${current.eyebrow}</p>
    <h1 class="reel-title reel-in reel-in-2">${current.titleHtml}</h1>
    <p class="reel-sub reel-in reel-in-3">${current.sub}</p>
    ${cta}
  `;

  [...progress.children].forEach((el, i) => {
    el.className = `reel-progress-seg${i === beat ? " is-active" : i < beat ? " is-done" : ""}`;
  });
  [...dots.children].forEach((el, i) => {
    el.classList.toggle("is-active", i === beat);
    el.setAttribute("aria-current", i === beat ? "true" : "false");
  });

  schedule();
}

dots.addEventListener("click", (e) => {
  const btn = e.target.closest("[data-i]");
  if (!btn) return;
  go(Number(btn.dataset.i));
});

pauseBtn.addEventListener("click", (e) => {
  e.stopPropagation();
  paused = !paused;
  pauseBtn.textContent = paused ? "▶" : "❚❚";
  pauseBtn.setAttribute("aria-label", paused ? "המשך" : "השהה");
  schedule();
});

function pointerDown(e) {
  touchX = e.clientX ?? e.touches?.[0]?.clientX ?? null;
}

function pointerUp(e) {
  const start = touchX;
  touchX = null;
  if (start == null) return;
  if (e.target.closest("a,button")) return;
  const end = e.clientX ?? e.changedTouches?.[0]?.clientX ?? start;
  const dx = end - start;
  if (Math.abs(dx) > 40) {
    go(beat + (dx < 0 ? 1 : -1));
    return;
  }
  const w = stage.clientWidth || window.innerWidth;
  if (end < w * 0.33) go(beat + 1);
  else if (end > w * 0.66) go(beat - 1);
}

stage.addEventListener("mousedown", pointerDown);
stage.addEventListener("mouseup", pointerUp);
stage.addEventListener("touchstart", pointerDown, { passive: true });
stage.addEventListener("touchend", pointerUp);

copy.addEventListener("click", (e) => {
  if (e.target.closest("a")) e.stopPropagation();
});

render();
