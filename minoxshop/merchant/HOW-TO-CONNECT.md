# איך לחבר את MinoxShop ל-Google Shopping

## מה כבר מוכן כאן
פיד מלא לכל המוצרים:
- `public/feeds/minox-google-merchant.tsv`
- גם ב־`minoxshop/merchant/google-merchant.tsv`

## שלב A — פיד שעובד עכשיו (בלי קוד Minox)
ראה גם `SHOPPING-NOW.md` לצ׳קליסט מלא.

ב-Merchant Center → Products → Data sources → Scheduled fetch:

```
https://raw.githubusercontent.com/ghzjfy-stack/barbero-shop/cursor/minox-shopping-now-75a4/public/feeds/minox-google-merchant.tsv
```

אחרי מיזוג ל־`cursor/fix-formatted-hero-75a4`:

```
https://raw.githubusercontent.com/ghzjfy-stack/barbero-shop/cursor/fix-formatted-hero-75a4/public/feeds/minox-google-merchant.tsv
```

(ה־`link` בפיד מצביע ל־`minox-shop.co.il/product/...` — זה תקין.)

ואז **Fetch now**.

## שלב B — חייב קוד האתר של Minox (אחרת לא תופיעו באורגני/Shopping חזק)
דפי `/product/...` קיימים למשתמש, אבל גוגל מקבל SPA ריק:
- אותו `<title>` לכל דף
- `canonical` לדף הבית
- אין JSON-LD למוצר
- sitemap בלי `/product/`
- `/feeds/google-merchant.tsv` מחזיר HTML

כדי לתקן את זה צריך את **ריפו GitHub / פרויקט Vercel של minox-shop**.
בלי זה אי אפשר לדחוף דיפלוי ל־`minox-shop.co.il`.

### מה לתקן בריפו Minox (כשייפתח)
1. שים את ה־TSV ב־`public/feeds/google-merchant.tsv`
2. ב־`vercel.json` — אל תפנה `/feeds/*` ל־`index.html` (העתק את ההגדרה מ־`vercel.json` כאן)
3. לכל `/product/:id` — title / canonical / og / JSON-LD Product **ב־HTML** (לא רק ב־JS)
4. הוסף את כל ה־product URLs ל־`sitemap.xml`
5. Search Console → שליחת sitemap מחדש
