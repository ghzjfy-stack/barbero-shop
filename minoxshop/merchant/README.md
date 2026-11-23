# Minox Shop — Google Merchant readiness kit

**Site:** https://www.minox-shop.co.il  
**Generated for:** all 19 live catalog products (incl. Amazon Basic Care + Shapiro)

## What went wrong earlier
PR #255 added Merchant feed + product pages to **BARBERO** (clippers). That does **not** help Minox Shop.

## What’s broken on Minox today (live check)
| Check | Status |
|---|---|
| Real feed at `/feeds/google-merchant.tsv` | ❌ Returns HTML SPA, not TSV |
| Unique product landing URLs | ❌ `/shop` redirects to `/#products` — all products share one page |
| Product JSON-LD / GTIN on pages | ❌ Missing |
| Sitemap product URLs | ❌ Only `/`, `/shop`, `/articles`, `/club`, `/search` |
| Shipping for IL | ✅ Site: free home delivery (use `0 ILS` in feed) |

Without **unique product links**, Merchant will keep disapproving / suppressing offers. A perfect TSV alone is not enough.

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
