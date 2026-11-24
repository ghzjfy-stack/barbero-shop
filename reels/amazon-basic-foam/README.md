# Amazon Basic Care — curiosity launch reel

| File | Use |
|---|---|
| `LAUNCH-CONCEPT.md` | Hook ranking + Grok-polished beat sheet |
| `CAPTION.md` | Hebrew caption for IG/TikTok |
| `scripts/abc_foam_curiosity_reel.py` | PIL + ffmpeg renderer |

## Render

```bash
# assets already at /tmp/minox-amazon/{box,cans}.png
python3 scripts/abc_foam_curiosity_reel.py
```

Outputs:
- `/tmp/abc-foam-curiosity/MinoxShop_ABC_curiosity_15s.mp4`
- `/tmp/abc-foam-curiosity/MinoxShop_ABC_curiosity_COVER.jpg`
- `/opt/cursor/artifacts/DOWNLOAD_MinoxShop_ABC_curiosity_*`

Rules enforced: Hebrew chips only · CTA הקישור בפרופיל · no Rogaine compare on screen · no Barbero · soft room tone · price after ~9.4s.
