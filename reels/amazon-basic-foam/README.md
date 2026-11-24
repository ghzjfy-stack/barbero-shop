# Amazon Basic Care — curiosity launch reel

| File | Use |
|---|---|
| `LAUNCH-CONCEPT.md` | Hook ranking + beat sheet |
| `CAPTION.md` | Organic Hebrew caption (IG / TikTok / Shorts) |
| `CAPTION-BOOST.md` | Soft caption if trying in-app Boost |
| `scripts/abc_foam_curiosity_reel.py` | PIL + ffmpeg renderer |

## Render

```bash
python3 scripts/abc_foam_curiosity_reel.py
```

Outputs:
- `/tmp/abc-foam-curiosity/MinoxShop_ABC_curiosity_15s.mp4`
- `/tmp/abc-foam-curiosity/MinoxShop_ABC_curiosity_COVER.jpg`
- `/opt/cursor/artifacts/DOWNLOAD_MinoxShop_ABC_curiosity_*`

## Upload tricks (views)

Cross-platform (what actually moves hook rate / replays):

1. **First frame = question on screen** (already baked). Cover = hook frame.
2. **Mute-first**: chips carry the story — don’t rely on audio.
3. **Post 3–5 hook variants over a week** if one underperforms (same body, different first line).
4. **Pin a comment** with price + link reminder after publish.
5. **Reply to early comments with a new Short** — algorithm loves that loop.

### YouTube Shorts
- Title (searchable): `מינוקסידיל 5% קצף לגברים | Black Friday 395₪`
- Description: first line = same promise as chips; add `#Shorts` optional.
- Shorts **cannot** set a custom cover — upload `MinoxShop_ABC_curiosity_YT.mp4` (or the main file after re-render): it holds the BF+395 cover for ~0.8s at frame 0. In upload → choose that first frame as the thumbnail.
- Don’t start with logo/intro after the cover hold — cold open into the curiosity beat.

### Instagram Reels
- Paste `CAPTION.md`. 3–5 hashtags max.
- If Boost blocked → Ads Manager (Health), not more creative edits.
- Story share same day with “הקישור בפרופיל”.

### TikTok
- Same file. Native caption. Trend sound optional — **don’t replace** our bed if it kills the cut sync; duplicate post to test a trend sound once.

## Rules
Hebrew chips · CTA הקישור בפרופיל · no Barbero · soft loop ending · clarity beat spells minoxidil + hair job.
