(() => {
  const stage = document.getElementById("stage");
  const afterClip = document.getElementById("afterClip");
  const softEdge = document.getElementById("softEdge");
  const handle = document.getElementById("handle");
  const range = document.getElementById("monthRange");
  const monthWord = document.getElementById("monthWord");
  const monthHint = document.getElementById("monthHint");
  const monthButtons = [...document.querySelectorAll(".month")];

  const HINTS = [
    { max: 0.75, word: "חודש 0", hint: "תחילת הדרך" },
    { max: 2.5, word: "חודש 2", hint: "השיער מתחיל להתחזק" },
    { max: 4.5, word: "חודש 4", hint: "צפיפות ניכרת מהשטח" },
    { max: 6.1, word: "חודש 6", hint: "תוצאה מלאה יותר · משתנה בין אנשים" },
  ];

  const afterImg = afterClip.querySelector("img.after");

  let months = Number(range.value) || 0.4;
  let dragging = false;
  let taught = false;

  const clamp = (n, a, b) => Math.min(b, Math.max(a, n));

  function syncStageWidth() {
    const w = `${stage.clientWidth}px`;
    stage.style.setProperty("--stage-w", w);
    if (afterImg) afterImg.style.width = w;
  }

  function monthsToProgress(m) {
    // Honest pacing: little change early, clearer by month 4
    const t = clamp(m / 6, 0, 1);
    return Math.pow(t, 0.85);
  }

  function nearestMonthMark(m) {
    const marks = [0, 2, 4, 6];
    return marks.reduce((best, cur) => (Math.abs(cur - m) < Math.abs(best - m) ? cur : best));
  }

  function apply(m, { snapButtons = true } = {}) {
    months = clamp(m, 0, 6);
    const progress = monthsToProgress(months);
    const pct = `${(progress * 100).toFixed(2)}%`;

    afterClip.style.width = pct;
    softEdge.style.left = `calc(${pct} - 18px)`;
    handle.style.left = pct;
    stage.style.setProperty("--handle", pct);

    range.value = String(months);
    range.setAttribute("aria-valuenow", String(Math.round(months * 10) / 10));

    const copy = HINTS.find((h) => months <= h.max) || HINTS[HINTS.length - 1];
    monthWord.textContent = copy.word;
    monthHint.textContent = copy.hint;
    range.setAttribute("aria-valuetext", `${copy.word} — ${copy.hint}`);

    if (snapButtons) {
      const active = nearestMonthMark(months);
      monthButtons.forEach((btn) => {
        btn.classList.toggle("is-active", Number(btn.dataset.m) === active);
      });
    }
  }

  function pointerToMonths(clientX) {
    const rect = stage.getBoundingClientRect();
    const x = clamp(clientX - rect.left, 0, rect.width);
    const progress = rect.width ? x / rect.width : 0;
    // Invert the ease used in monthsToProgress
    const t = clamp(progress, 0, 1);
    return Math.pow(t, 1 / 0.85) * 6;
  }

  function onPointerDown(event) {
    dragging = true;
    taught = true;
    stage.setPointerCapture?.(event.pointerId);
    apply(pointerToMonths(event.clientX));
  }

  function onPointerMove(event) {
    if (!dragging) return;
    apply(pointerToMonths(event.clientX));
  }

  function onPointerUp(event) {
    if (!dragging) return;
    dragging = false;
    try {
      stage.releasePointerCapture?.(event.pointerId);
    } catch (_) {
      /* ignore */
    }
  }

  stage.addEventListener("pointerdown", onPointerDown);
  stage.addEventListener("pointermove", onPointerMove);
  stage.addEventListener("pointerup", onPointerUp);
  stage.addEventListener("pointercancel", onPointerUp);

  range.addEventListener("input", () => {
    taught = true;
    apply(Number(range.value));
  });

  monthButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      taught = true;
      animateTo(Number(btn.dataset.m), 520);
    });
  });

  function animateTo(target, duration = 700) {
    const from = months;
    const to = clamp(target, 0, 6);
    const start = performance.now();
    const tick = (now) => {
      const u = clamp((now - start) / duration, 0, 1);
      const eased = 1 - Math.pow(1 - u, 3);
      apply(from + (to - from) * eased);
      if (u < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }

  // First-visit teach: gentle drag toward month 4
  syncStageWidth();
  apply(0.35);
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!reduceMotion) {
    window.setTimeout(() => {
      if (taught) return;
      animateTo(4, 1600);
    }, 700);
  }

  window.addEventListener("resize", () => {
    syncStageWidth();
    apply(months);
  });
})();
