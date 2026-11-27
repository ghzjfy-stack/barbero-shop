# Google Shopping — חיבור עכשיו (MinoxShop)

## 1) כתובת הפיד (העתק כמו שזה)
```
https://raw.githubusercontent.com/ghzjfy-stack/barbero-shop/cursor/minox-shopping-now-75a4/public/feeds/minox-google-merchant.tsv
```

גיבוי (אותו קובץ אחרי מיזוג ל־fix-formatted-hero):
```
https://raw.githubusercontent.com/ghzjfy-stack/barbero-shop/cursor/fix-formatted-hero-75a4/public/feeds/minox-google-merchant.tsv
```

## 2) ב־Google Merchant Center (חובה עכשיו)
1. היכנס ל־[Merchant Center](https://merchants.google.com) של **minox-shop.co.il**
2. **Products → Data sources**
3. אם אין מקור: **Add product data source → Scheduled fetch**
4. הדבק את כתובת הפיד למעלה
5. File type: **TSV / Tab-delimited** · Encoding: **UTF-8** · Country: **Israel** · Language: **Hebrew**
6. **Fetch now** / Fetch
7. חכה לסיום העיבוד → **Products → Diagnostics / Needs attention**
8. תקן רק מה שמסומן באדום (אם יש)

## 3) בדיקות חובה בחשבון
- האתר `https://www.minox-shop.co.il` **מאומת** (Website verification)
- משלוח לישראל מוגדר (בפיד כבר `IL:::0.00 ILS` = משלוח חינם)
- מדיניות החזרות / יצירת קשר ממולאות ב־Business info

## 4) מה כבר תקין בפיד
- 19 מוצרים · לינקים + תמונות חיים (200)
- מחירים ב־ILS
- GTIN איפה שיש · `identifier_exists=no` איפה שאין
- `kirkland-foam-woman` = **out_of_stock** (תואם לאתר)
- מארזים כפולים = `multipack` (לא bundle)

## 5) מגבלה חשובה
בלי קוד האתר של Minox אי אפשר לתקן SEO של דפי מוצר (canonical/JSON-LD).  
Free Listings עדיין יכולים לעלות מהפיד אם Merchant מאשר — אבל דפי נחיתה חלשים עלולים לעכב/להחליש חשיפה.

ברגע שיש ריפו מהשותף — משלימים SEO + sitemap + פיד על הדומיין עצמו.
