#!/usr/bin/env python3
"""v26 CapCut-style cream shelf outro — mirror bounce + wink sparkle + 6 site products."""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

OUT = Path("/tmp/foam-v26/frames")
OUT.mkdir(parents=True, exist_ok=True)
PACKS = Path("/tmp/foam-v26/packs/clean")
W, H, FPS = 1080, 1920, 30
N = 120  # 4.0s — room for row2 + CTA hold
HEB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
HEB_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

CREAM = (245, 240, 232)
CREAM2 = (252, 248, 242)
WHITE = (255, 255, 255)
NAVY = (18, 32, 58)
GOLD = (196, 158, 86)
INK = (28, 32, 44)


def font(size: int, bold: bool = True):
    return ImageFont.truetype(HEB if bold else HEB_R, size)


def ease_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def ease_out_back(t: float) -> float:
    t = max(0.0, min(1.0, t))
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def cream_field() -> Image.Image:
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    # soft radial cream + gentle vignette
    cx, cy = W / 2, H * 0.42
    r = np.sqrt(((xx - cx) / (W * 0.72)) ** 2 + ((yy - cy) / (H * 0.85)) ** 2)
    mix = np.clip(1 - 0.18 * r, 0.78, 1.0)
    base = np.array(CREAM, dtype=np.float32)
    hi = np.array(CREAM2, dtype=np.float32)
    arr = base + (hi - base) * mix[:, :, None]
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    im = Image.fromarray(arr, "RGB").convert("RGBA")
    # faint warm grainless wash
    wash = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(wash)
    d.ellipse((-180, 900, 520, 1700), fill=(255, 220, 180, 28))
    d.ellipse((650, -120, 1280, 520), fill=(255, 235, 210, 22))
    return Image.alpha_composite(im, wash.filter(ImageFilter.GaussianBlur(70)))


def fit_h(im: Image.Image, th: int) -> Image.Image:
    w0, h0 = im.size
    return im.resize((max(1, int(round(w0 * th / h0))), th), Image.Resampling.LANCZOS)


def fit_max(im: Image.Image, mw: int, mh: int) -> Image.Image:
    w0, h0 = im.size
    s = min(mw / w0, mh / h0, 1.0)
    return im.resize((max(1, int(round(w0 * s))), max(1, int(round(h0 * s)))), Image.Resampling.LANCZOS)


def reflection(p: Image.Image, op: float = 0.28, frac: float = 0.28) -> Image.Image:
    f = p.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    f = ImageEnhance.Brightness(f).enhance(0.42)
    w, h = f.size
    # short mirror — CapCut floor look (keep short so card never clips)
    h2 = max(8, int(h * frac))
    f = f.crop((0, 0, w, h2))
    fade = Image.new("L", (w, h2), 0)
    d = ImageDraw.Draw(fade)
    for i in range(h2):
        d.line([(0, i), (w, i)], fill=int(255 * op * max(0.0, 1 - i / (h2 * 0.92))))
    f.putalpha(fade)
    return f.filter(ImageFilter.GaussianBlur(3.2))


def soft_shadow(c: Image.Image, box: Image.Image, x: int, y: int, a: int = 100):
    sh = Image.new("RGBA", (box.size[0] + 60, 56), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([8, 14, box.size[0] + 48, 40], fill=(30, 22, 14, int(a * 0.55)))
    c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)), (x - 30, y + box.size[1] - 8))


def rounded_card(cw: int, ch: int, radius: int = 36) -> Image.Image:
    card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle([0, 0, cw - 1, ch - 1], radius, fill=WHITE + (255,))
    # inner soft top highlight
    hi = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    ImageDraw.Draw(hi).rounded_rectangle([6, 6, cw - 7, ch // 3], radius - 4, fill=(255, 255, 255, 40))
    return Image.alpha_composite(card, hi.filter(ImageFilter.GaussianBlur(8)))


def card_shadow(cw: int, ch: int) -> Image.Image:
    sh = Image.new("RGBA", (cw + 80, ch + 80), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([20, 28, cw + 50, ch + 55], 40, fill=(20, 16, 12, 55))
    return sh.filter(ImageFilter.GaussianBlur(28))


def wink_sparkle(layer: Image.Image, cx: int, cy: int, phase: float, scale: float = 1.0):
    """CapCut-style cross wink sparkle — peaks mid phase."""
    pulse = math.sin(math.pi * max(0.0, min(1.0, phase)))
    if pulse < 0.05:
        return
    a = int(255 * pulse)
    sp = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(sp)
    r = int(18 * scale * (0.55 + 0.45 * pulse))
    # cross arms
    d.line([(cx - r, cy), (cx + r, cy)], fill=(255, 250, 230, a), width=max(2, int(3 * scale)))
    d.line([(cx, cy - r), (cx, cy + r)], fill=(255, 250, 230, a), width=max(2, int(3 * scale)))
    # diamond core
    core = max(2, int(4 * scale * pulse))
    d.ellipse([cx - core, cy - core, cx + core, cy + core], fill=(255, 255, 255, a))
    # soft bloom
    bloom = sp.filter(ImageFilter.GaussianBlur(2))
    layer.alpha_composite(bloom)
    layer.alpha_composite(sp)


def draw_text(im, text, y, size, fill, alpha=255, bold=True):
    f = font(size, bold)
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    bb = d.textbbox((0, 0), text, font=f, language="he")
    x = (W - (bb[2] - bb[0])) // 2 - bb[0]
    d.text((x, y + 2), text, font=f, fill=(0, 0, 0, int(70 * alpha / 255)), language="he")
    d.text((x, y), text, font=f, fill=(*fill, alpha), language="he")
    im.alpha_composite(layer)


def pill(text: str, fill, fg, pad_x=36, pad_y=18, size=34, bold=True) -> Image.Image:
    f = font(size, bold)
    tmp = Image.new("RGBA", (W, 200), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    bb = d.textbbox((0, 0), text, font=f, language="he")
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    pw, ph = tw + pad_x * 2, th + pad_y * 2
    pill_im = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    d2 = ImageDraw.Draw(pill_im)
    d2.rounded_rectangle([0, 0, pw - 1, ph - 1], ph // 2, fill=fill)
    d2.text((pad_x - bb[0], pad_y - bb[1]), text, font=f, fill=fg, language="he")
    return pill_im


def load_packs():
    men_h = 210
    row2_h = 150
    rog = fit_h(Image.open(PACKS / "rogaine_men.png").convert("RGBA"), men_h)
    kirk = fit_max(Image.open(PACKS / "kirkland.png").convert("RGBA"), 230, men_h)
    mem = fit_h(Image.open(PACKS / "members.png").convert("RGBA"), men_h)
    # women MUST stay fully inside card — compact full box+cans
    wom = fit_max(Image.open(PACKS / "women.png").convert("RGBA"), 230, row2_h)
    shampoo = fit_h(Image.open(PACKS / "shampoo.png").convert("RGBA"), row2_h + 8)
    shapiro = fit_max(Image.open(PACKS / "shapiro.png").convert("RGBA"), 200, row2_h)
    logo = Image.open(PACKS / "logo.png").convert("RGBA")
    # prefer classic chips if available
    btn = None
    url = None
    bp = PACKS / "chip_cta_btn.png"
    up = PACKS / "chip_cta_url.png"
    if bp.exists():
        btn = Image.open(bp).convert("RGBA")
        btn.thumbnail((620, 120), Image.Resampling.LANCZOS)
    if up.exists():
        url = Image.open(up).convert("RGBA")
        url.thumbnail((420, 90), Image.Resampling.LANCZOS)
    return {
        "men": [rog, kirk, mem],
        "row2": [wom, shampoo, shapiro],
        "logo": logo,
        "btn": btn,
        "url": url,
    }


def layout_row(packs: list[Image.Image], gap: int = 28) -> list[tuple[Image.Image, int]]:
    """Return (pack, x_offset_from_row_left) centered later."""
    widths = [p.size[0] for p in packs]
    total = sum(widths) + gap * (len(packs) - 1)
    x = 0
    out = []
    for p, w in zip(packs, widths):
        out.append((p, x))
        x += w + gap
    return out, total


def frame_at(i: int, assets: dict) -> Image.Image:
    t = i / max(1, N - 1)
    im = cream_field()

    # --- Logo (classic reel) ---
    logo = assets["logo"]
    la = ease_out(min(1.0, t / 0.10))
    if la > 0.02:
        lw, lh = logo.size
        lx, ly = (W - lw) // 2, 70
        lg = logo.copy()
        lg.putalpha(lg.split()[-1].point(lambda a: int(a * la)))
        # soft logo plate
        plate = Image.new("RGBA", (lw + 28, lh + 28), (0, 0, 0, 0))
        ImageDraw.Draw(plate).rounded_rectangle([0, 0, lw + 27, lh + 27], 18, fill=(255, 255, 255, int(230 * la)))
        im.alpha_composite(plate.filter(ImageFilter.GaussianBlur(0.5)), (lx - 14, ly - 14))
        im.alpha_composite(lg, (lx, ly))
        # wink on logo corner
        wink_sparkle(im, lx + lw - 8, ly + 10, (t - 0.08) / 0.18, scale=0.85)

    # Timing beats (CapCut feel)
    # 0.00–0.12 card appears
    # 0.10–0.42 men bounce in stagger
    # 0.38–0.55 card expands + row2 bounce
    # 0.55–0.72 CTA + URL
    # 0.72–1.00 hold + soft pulse

    men = assets["men"]
    row2 = assets["row2"]
    men_layout, men_w = layout_row(men, gap=22)
    row2_layout, row2_w = layout_row(row2, gap=20)

    # Card geometry
    pad_x = 56
    pad_top = 44
    pad_bot_1 = 56
    pad_bot_2 = 72  # critical: room for row2 + short mirror, no crop
    men_h = max(p.size[1] for p in men)
    row2_h = max(p.size[1] for p in row2)
    refl_h = int(men_h * 0.26) + 6

    expand = ease_out(min(1.0, max(0.0, (t - 0.36) / 0.16)))
    content_w = max(men_w, row2_w) + pad_x * 2
    # keep generous side margin so nothing kisses the rounded clip
    cw = int(min(1000, max(content_w + 40, 860)))
    ch1 = pad_top + men_h + refl_h + pad_bot_1
    ch2 = pad_top + men_h + 48 + row2_h + int(row2_h * 0.26) + pad_bot_2
    ch = int(ch1 + (ch2 - ch1) * expand)

    card_appear = ease_out(min(1.0, t / 0.12))  # no overshoot on card size
    if card_appear < 0.02:
        return im.convert("RGB").convert("RGBA")

    # card vertical position — higher when single row, settles as expands
    cy0 = 360
    cy1 = 300
    cy = int(cy0 + (cy1 - cy0) * expand)
    cx = (W - cw) // 2

    # gentle pop without clipping — clamp scale <= 1 relative to designed card
    scale = 0.92 + 0.08 * card_appear
    scw, sch = int(cw * scale), int(ch * scale)
    scx, scy = (W - scw) // 2, cy + (ch - sch) // 2
    # absolute safe inset inside rounded card (px in scaled space)
    safe = int(28 * scale)

    # shadow + card
    sh = card_shadow(scw, sch)
    im.alpha_composite(sh, (scx - 40, scy - 20))
    card = rounded_card(scw, sch, radius=34)
    # slight alpha during appear
    if card_appear < 1:
        a = card.split()[-1].point(lambda v: int(v * min(1.0, 0.4 + 0.6 * card_appear)))
        card.putalpha(a)
    im.alpha_composite(card, (scx, scy))

    # inner product stage coords (map from unscaled card space)
    def map_xy(x_in_card: int, y_in_card: int):
        return scx + int(x_in_card * scale), scy + int(y_in_card * scale)

    def place_pack(p, x_card, y_card, local, bounce=80, refl_frac=0.26):
        """Place pack with Y bounce; clamp scale<=1 and keep inside card safe inset."""
        local_c = max(0.0, min(1.0, local))
        # overshoot only on Y, never on size
        over = max(0.0, local - 1.0)
        dy = int((1 - local_c) * bounce - over * 10)
        ps = 0.88 + 0.12 * local_c  # max 1.0
        pw = max(1, int(p.size[0] * ps * scale))
        ph = max(1, int(p.size[1] * ps * scale))
        pp = p.resize((pw, ph), Image.Resampling.LANCZOS)
        if local_c < 1:
            pp = pp.copy()
            pp.putalpha(pp.split()[-1].point(lambda a: int(a * local_c)))
        px = scx + int(x_card * scale) + (int(p.size[0] * scale) - pw) // 2
        py = scy + int(y_card * scale) + dy
        # reserve room for short mirror under pack
        mirror_room = int(ph * refl_frac) + 10
        px = max(scx + safe, min(px, scx + scw - safe - pw))
        py = max(scy + safe // 2, min(py, scy + sch - safe - ph - mirror_room))
        soft_shadow(im, pp, px, py, a=int(110 * local_c))
        if local_c > 0.55:
            ref = reflection(
                pp,
                op=0.24 * min(1.0, (local_c - 0.55) / 0.45),
                frac=refl_frac,
            )
            ry = py + pp.size[1] - 4
            if ry + ref.size[1] <= scy + sch - safe // 2:
                im.alpha_composite(ref, (px, ry))
        im.alpha_composite(pp, (px, py))
        return px, py, pw, ph

    # --- Men row bounce ---
    men_left = (cw - men_w) // 2
    men_y = pad_top
    for idx, (p, ox) in enumerate(men_layout):
        start = 0.10 + idx * 0.055
        local = ease_out_back(min(1.0, max(0.0, (t - start) / 0.16)))
        if local <= 0.01:
            continue
        px, py, pw, ph = place_pack(p, men_left + ox, men_y, local, bounce=90, refl_frac=0.24)
        wink_sparkle(im, px + pw // 2 + 18, py + 24, (t - (start + 0.14)) / 0.12, scale=0.9)

    # --- Row 2: women + shampoo + new ---
    if expand > 0.20:
        row2_left = (cw - row2_w) // 2
        row2_y = pad_top + men_h + 40
        chip_a = int(255 * ease_out(min(1.0, max(0.0, (t - 0.46) / 0.12))))
        row2_positions = []
        for idx, (p, ox) in enumerate(row2_layout):
            start = 0.42 + idx * 0.05
            local = ease_out_back(min(1.0, max(0.0, (t - start) / 0.15)))
            if local <= 0.01:
                row2_positions.append(None)
                continue
            px, py, pw, ph = place_pack(p, row2_left + ox, row2_y, local, bounce=60, refl_frac=0.20)
            row2_positions.append((px, py, pw, ph))
            wink_sparkle(im, px + pw // 2 + 12, py + 18, (t - (start + 0.12)) / 0.12, scale=0.8)

        # chips ONLY after packs landed — above women (0) and shapiro (2)
        if chip_a > 24 and row2_positions[0] and row2_positions[2]:
            chip = pill("גם לנשים", GOLD + (chip_a,), (255, 255, 255, chip_a), pad_x=16, pad_y=7, size=20)
            chip2 = pill("חדש באתר", NAVY + (chip_a,), (255, 255, 255, chip_a), pad_x=14, pad_y=7, size=18)
            wx, wy, ww, wh = row2_positions[0]
            sx, sy, sw, sh_ = row2_positions[2]
            # float just above pack tops, clamped inside card
            cy_chip = max(scy + safe, wy - chip.size[1] - 16)
            cx1 = max(scx + safe, min(wx + (ww - chip.size[0]) // 2, scx + scw - safe - chip.size[0]))
            cx2 = max(scx + safe, min(sx + (sw - chip2.size[0]) // 2, scx + scw - safe - chip2.size[0]))
            im.alpha_composite(chip, (cx1, cy_chip))
            im.alpha_composite(chip2, (cx2, cy_chip))

    # --- CTA zone ---
    cta_t = ease_out(min(1.0, max(0.0, (t - 0.56) / 0.14)))
    if cta_t > 0.02:
        # headline
        draw_text(im, "מוכנים לבחור", int(scy + sch + 36 + (1 - cta_t) * 24), 44, INK, int(255 * cta_t))
        # gold rule wink
        if cta_t > 0.4:
            rw = int(120 * ease_out((cta_t - 0.4) / 0.6))
            d = ImageDraw.Draw(im)
            yy = int(scy + sch + 92)
            d.rounded_rectangle([(W - rw) // 2, yy, (W + rw) // 2, yy + 3], 2, fill=GOLD + (int(240 * cta_t),))
            wink_sparkle(im, (W + rw) // 2 - 4, yy + 1, (t - 0.68) / 0.15, scale=0.7)

        # button
        btn = assets["btn"]
        url = assets["url"]
        pulse = 1.0 + 0.035 * math.sin(t * math.pi * 4) * max(0.0, (t - 0.7) / 0.3)
        if btn is not None:
            bw, bh = int(btn.size[0] * pulse), int(btn.size[1] * pulse)
            b = btn.resize((bw, bh), Image.Resampling.LANCZOS)
            if cta_t < 1:
                b = b.copy()
                b.putalpha(b.split()[-1].point(lambda a: int(a * cta_t)))
            bx = (W - bw) // 2
            by = int(scy + sch + 118 + (1 - cta_t) * 30)
            # button shadow
            soft_shadow(im, b, bx, by, a=int(130 * cta_t))
            im.alpha_composite(b, (bx, by))
            by_url = by + bh + 18
        else:
            # fallback navy pill
            b = pill("לרכישה וצבירת נקודות", NAVY + (255,), (255, 255, 255, 255), pad_x=40, pad_y=22, size=36)
            bw, bh = int(b.size[0] * pulse), int(b.size[1] * pulse)
            b = b.resize((bw, bh), Image.Resampling.LANCZOS)
            if cta_t < 1:
                b.putalpha(b.split()[-1].point(lambda a: int(a * cta_t)))
            bx = (W - bw) // 2
            by = int(scy + sch + 118 + (1 - cta_t) * 30)
            soft_shadow(im, b, bx, by, a=int(130 * cta_t))
            im.alpha_composite(b, (bx, by))
            by_url = by + bh + 18

        if url is not None:
            uw, uh = url.size
            u = url.copy()
            if cta_t < 1:
                u.putalpha(u.split()[-1].point(lambda a: int(a * cta_t)))
            im.alpha_composite(u, ((W - uw) // 2, by_url))
        else:
            u = pill("minox-shop.co.il", (255, 255, 255, 245), NAVY + (255,), pad_x=28, pad_y=14, size=28, bold=False)
            # stroke
            stroke = Image.new("RGBA", u.size, (0, 0, 0, 0))
            ImageDraw.Draw(stroke).rounded_rectangle([1, 1, u.size[0] - 2, u.size[1] - 2], u.size[1] // 2, outline=NAVY + (180,), width=2)
            u = Image.alpha_composite(u, stroke)
            if cta_t < 1:
                u.putalpha(u.split()[-1].point(lambda a: int(a * cta_t)))
            im.alpha_composite(u, ((W - u.size[0]) // 2, by_url))

    return im


def main():
    assets = load_packs()
    # sanity: ensure row2 products fully fit card width with margin
    _, men_w = layout_row(assets["men"], 22)
    _, row2_w = layout_row(assets["row2"], 20)
    print("men_w", men_w, "row2_w", row2_w)
    assert men_w < 980 and row2_w < 980, "products too wide for card"

    for i in range(N):
        fr = frame_at(i, assets)
        fr.convert("RGB").save(OUT / f"f_{i:04d}.jpg", quality=95, optimize=True)
        if i % 30 == 0:
            print("frame", i)
    # QA stills
    for qi in (15, 45, 70, 95, 115):
        Image.open(OUT / f"f_{qi:04d}.jpg").save(f"/tmp/foam-v26/qa/outro_{qi}.jpg", quality=92)
    print("DONE frames", N)


if __name__ == "__main__":
    main()
