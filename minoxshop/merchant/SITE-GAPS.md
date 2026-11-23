# Code gaps on minox-shop.co.il (must fix in Minox repo)

## 1. Unique product URLs (blocking)
Today: `/shop` → redirect → `/#products`  
Needed: `/product/rogaine-double-man`, `/product/amazon-basic-foam-man`, … for every SKU

Each page must show: title, price (ILS), availability, primary image, Add to cart, matching feed data.

## 2. Hosted Merchant feed
Serve this kit’s `google-merchant.tsv` at:

`https://www.minox-shop.co.il/feeds/google-merchant.tsv`

Content-Type: `text/tab-separated-values; charset=utf-8`  
(not the SPA `index.html` fallback)

## 3. Product JSON-LD
On every product page inject `schema.org/Product` with `gtin13`/`mpn`, `offers.price`, `offers.availability`.

## 4. Sitemap
Add all `/product/{id}` URLs (+ image sitemap entries).

## 5. Image policy reminders
- Primary `image_link` = single clean box / hero (no 2×2 grid collage)
- Extra cans/bottles go in `additional_image_link`
- Especially risk: `rogaine-year-man` 12-can collage
