# Minox Shop — Google Merchant readiness kit

**Site:** https://www.minox-shop.co.il  
**Generated for:** all 19 live catalog products (incl. Amazon Basic Care + Shapiro)

## What went wrong earlier
PR #255 added Merchant feed + product pages to **BARBERO** (clippers). That does **not** help Minox Shop.

## Live feed (working URL for Merchant Center)

`minox-shop.co.il/feeds/...` still serves the SPA HTML (Minox source is not in this repo).
Use this hosted TSV until the Minox Vercel project serves `/feeds` as a static file:

- **Preferred (after this PR deploys):** `https://www.barbero.co.il/feeds/minox-google-merchant.tsv`
- **GitHub raw (works immediately after merge to the PR branch / main):**  
  `https://raw.githubusercontent.com/ghzjfy-stack/barbero-shop/cursor/minox-merchant-feed-fix-75a4/public/feeds/minox-google-merchant.tsv`

In Merchant Center → Products → Data sources → edit feed URL → paste one of the above → Fetch now.

## What’s broken on Minox today (live check)
| Check | Status |
|---|---|
| Real feed at `minox-shop.co.il/feeds/google-merchant.tsv` | ❌ Returns HTML SPA, not TSV |
| Hosted feed in this repo (`/feeds/minox-google-merchant.tsv`) | ✅ TSV ready |
| Unique product landing URLs | ⚠️ `/product/{id}` exists as SPA route (same shell meta) |
| Product JSON-LD / GTIN on pages | ❌ Missing in HTML |
| Shipping for IL | ✅ Site: free home delivery (use `0 ILS` in feed) |

Without crawlable product HTML (JSON-LD / unique meta), Shopping ads stay weak even if the feed is Active.

## Files in this folder
- `google-merchant.tsv` — full feed for all 19 products (upload or host after product pages exist)
- `PRODUCT-IDENTIFIERS.md` — GTIN/MPN sources + store-bundle rules
- `SITE-GAPS.md` — code changes required in the Minox Shop repo

## How to use (after product pages exist)
1. Deploy `/product/{id}` pages + host this TSV at `https://www.minox-shop.co.il/feeds/google-merchant.tsv`
2. Merchant Center → Products → Data sources → Scheduled fetch (IL / Hebrew)
3. Confirm Business info: shipping `0 ILS`, returns 14 days, contact

## Blocker for this agent
Minox Shop **source code is not in this GitHub workspace** (only `barbero-shop` + marketing scripts).  
To wire the feed + product pages into the live site, open the Minox Shop repo here (or paste its GitHub URL).
