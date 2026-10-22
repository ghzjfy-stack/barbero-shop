export const announcements = [
  "100% יבוא מקורי מארה״ב",
  "משלוח מהיר לכל הארץ",
  "אחריות רשמית",
  "מתח אוניברסלי 100V–240V",
  "החלפה נוחה תוך 14 יום",
  "תשלום מאובטח",
];

export const FREE_SHIPPING = 499;
export const SHIPPING_FEE = 39;

export const categories = [
  "הכל",
  "מכונות תספורת",
  "מכונות גילוח",
  "טרימרים",
  "גילוח ידני",
  "טיפוח",
];

export const navLinks = [
  { label: "קולקציה", href: "#collection" },
  { label: "מכונות תספורת", href: "#collection", category: "מכונות תספורת" },
  { label: "גילוח", href: "#collection", category: "מכונות גילוח" },
  { label: "טיפוח", href: "#collection", category: "טיפוח" },
  { label: "אודות", href: "#about" },
];

export const trustItems = [
  {
    icon: "truck",
    title: "משלוח מהיר",
    text: "שליח עד הבית בכל הארץ, בדרך כלל תוך 2–5 ימי עסקים, עם מספר מעקב ברגע שהחבילה יוצאת.",
  },
  {
    icon: "bolt",
    title: "מתח אוניברסלי 100V–240V",
    text: "המכונות מגיעות מוכנות לשקע הישראלי. בלי ממיר, בלי מתאם, ובלי הפתעות בהפעלה הראשונה.",
  },
  {
    icon: "globe",
    title: "יבוא ישיר מארה״ב",
    text: "סחורה מקורית בלבד, מהמותג ועד אליכם. לא שוק אפור, לא מקביל, ולא חיקוי שנראה דומה.",
  },
  {
    icon: "shield",
    title: "אחריות רשמית",
    text: "אחריות יבואן מלאה ושירות לקוחות בעברית. אם משהו לא יושב נכון, יש למי לפנות.",
  },
];

export const serviceLinks = [
  { label: "מעקב הזמנה", page: "tracking" },
  { label: "משלוחים והחזרות", page: "shipping" },
  { label: "אחריות", page: "warranty" },
  { label: "שאלות נפוצות", page: "faq" },
  { label: "מדיניות פרטיות", page: "privacy" },
  { label: "תקנון", page: "terms" },
];

export const pages = {
  tracking: {
    title: "מעקב הזמנה",
    paragraphs: [
      "הזינו את מספר ההזמנה ממסך האישור. המעקב בדמו הזה נשמר בדפדפן בלבד.",
    ],
  },
  shipping: {
    title: "משלוחים והחזרות",
    paragraphs: [
      "משלוח לכל הארץ תוך 2–5 ימי עסקים. בקנייה מעל 499 ₪ המשלוח עלינו, ומתחת לסכום זה עלות המשלוח 39 ₪.",
      "חלון החלפה של 14 יום מיום קבלת המוצר, כשהפריט באריזתו המקורית ולא נעשה בו שימוש. מוצרי טיפוח שנפתחו אינם ניתנים להחזרה מטעמי היגיינה.",
      "איסוף עצמי אינו פעיל בתצוגה הזו. בקופה בוחרים כתובת למשלוח בלבד.",
    ],
  },
  warranty: {
    title: "אחריות רשמית",
    paragraphs: [
      "מכונות תספורת, גילוח וטרימרים מגיעים עם אחריות יבואן לשנתיים על מנוע ורכיבים חשמליים. בלאי סביר של להב או רשת אינו כלול.",
      "האחריות תקפה ליבוא של BARBERO בלבד, מול חשבונית. פונים אלינו בעברית, ואנחנו מתאמים בדיקה או החלפה בלי לשלוח אתכם למותג בחו״ל.",
    ],
  },
  faq: {
    title: "שאלות נפוצות",
    paragraphs: [
      "האם המכונה עובדת בישראל? כן. הדגמים בקטלוג הם 100V–240V ומתחברים לשקע ישראלי בלי ממיר.",
      "האם זה יבוא מקורי? כן. אנחנו מביאים את הסחורה ישירות מארה״ב, עם אחריות יבואן ולא דרך שוק מקביל.",
      "תוך כמה זמן זה מגיע? בדרך כלל 2–5 ימי עסקים מרגע האישור, עם מספר מעקב.",
      "אפשר להחליף דגם? כן, תוך 14 יום, כל עוד המוצר לא היה בשימוש והאריזה שמורה.",
    ],
  },
  privacy: {
    title: "מדיניות פרטיות",
    paragraphs: [
      "הפרטים שמוזנים בקופה ובניוזלטר נשמרים במכשיר הזה בלבד לצורך תצוגת הממשק. אין כאן שרת, סליקה, או רשימת תפוצה אמיתית.",
      "בדפדפן נשמרים תוכן העגלה ורשימת המשאלות, כדי שהבחירה לא תיעלם ברענון. אפשר למחוק אותם דרך ניקוי הנתונים של האתר.",
    ],
  },
  terms: {
    title: "תקנון",
    paragraphs: [
      "BARBERO בתצוגה הזו הוא ממשק חנות לדוגמה. הזמנה שמושלמת כאן אינה חיוב ואינה נשלחת לאספקה.",
      "המחירים, המלאי והדירוגים הם נתוני מצייני מקום לקטלוג. התמונות משמשות להמחשת האווירה של הבית.",
    ],
  },
};

export const products = [
  {
    id: "magic-clip",
    name: "מכונת תספורת מג׳יק קליפ",
    brand: "Wahl",
    category: "מכונות תספורת",
    rating: 4.9,
    reviews: 286,
    sku: "BRB-W-MC",
    voltage: "100–240V",
    origin: "ארה״ב",
    badge: "רב־מכר",
    stock: 14,
    image:
      "https://images.unsplash.com/photo-1512690459411-b9245aed614b?auto=format&fit=crop&w=1000&q=80",
    blurb:
      "להב מדורג, מנוע שקט ומשקל שמחזיק מעמד במשמרת שלמה. הבחירה של מספרות שמבקשות קו נקי בלי רעש מיותר.",
    variants: [
      { id: "cord", label: "עם כבל", price: 589 },
      { id: "cordless", label: "אלחוטי", price: 749, compareAt: 829 },
    ],
  },
  {
    id: "andis-master",
    name: "מכונת תספורת מאסטר",
    brand: "Andis",
    category: "מכונות תספורת",
    rating: 4.8,
    reviews: 194,
    sku: "BRB-A-MS",
    voltage: "100–240V",
    origin: "ארה״ב",
    badge: null,
    stock: 9,
    price: 629,
    image:
      "https://images.unsplash.com/photo-1621605815971-fbc98d665033?auto=format&fit=crop&w=1000&q=80",
    blurb:
      "מכונת כבל קלאסית עם ידית חלקה והתנגדות להב מדויקת. בנויה לעבודה יומיומית, לא לטרנד של עונה.",
  },
  {
    id: "series-9",
    name: "מכונת גילוח סדרה 9 פרו",
    brand: "Braun",
    category: "מכונות גילוח",
    rating: 4.9,
    reviews: 412,
    sku: "BRB-B-S9",
    voltage: "100–240V",
    origin: "ארה״ב",
    badge: "פרימיום",
    stock: 7,
    image:
      "https://images.unsplash.com/photo-1622286342621-4bd786c2447c?auto=format&fit=crop&w=1000&q=80",
    blurb:
      "גילוח צמוד בתנועה אחת, עם ראש גמיש שעוקב אחרי קו הלסת. נטענת, ומוכנה לשקע ישראלי.",
    variants: [
      { id: "graphite", label: "גרפיט", price: 1490, compareAt: 1690 },
      { id: "gold", label: "זהב", price: 1690 },
    ],
  },
  {
    id: "arc5",
    name: "מכונת גילוח ארק 5",
    brand: "Panasonic",
    category: "מכונות גילוח",
    rating: 4.7,
    reviews: 155,
    sku: "BRB-P-A5",
    voltage: "100–240V",
    origin: "ארה״ב",
    badge: null,
    stock: 11,
    price: 989,
    compareAt: 1120,
    image:
      "https://images.unsplash.com/photo-1503951914875-452162b0f3f1?auto=format&fit=crop&w=1000&q=80",
    blurb:
      "להב יפני ומנוע לינארי. לגילוח קרוב שנשאר שקט גם בבוקר השני, בלי לגרד את העור.",
  },
  {
    id: "goldfx",
    name: "טרימר קווי מתאר גולד",
    brand: "BaBylissPRO",
    category: "טרימרים",
    rating: 4.8,
    reviews: 203,
    sku: "BRB-BB-FX",
    voltage: "100–240V",
    origin: "ארה״ב",
    badge: null,
    stock: 16,
    price: 469,
    image:
      "https://images.unsplash.com/photo-1517832606299-7ae9b720a186?auto=format&fit=crop&w=1000&q=80",
    blurb:
      "טרימר צר לקווי זקן, פיאות ודיוק סביב האוזן. להב בציפוי זהב שמחליק על העור.",
  },
  {
    id: "merkur",
    name: "סכין גילוח בטיחותי 34C",
    brand: "Merkur",
    category: "גילוח ידני",
    rating: 4.9,
    reviews: 98,
    sku: "BRB-M-34C",
    voltage: null,
    origin: "גרמניה",
    badge: null,
    stock: 3,
    price: 189,
    image:
      "https://images.unsplash.com/photo-1582095133179-bfd08e2fc6b3?auto=format&fit=crop&w=1000&q=80",
    blurb:
      "סכין בטיחותי בשלושה חלקים, ראש סגור ומשקל נכון. למי שמעדיף טקס על פני חיפזון.",
  },
  {
    id: "proraso",
    name: "ערכת טיפוח זקן קלאסית",
    brand: "Proraso",
    category: "טיפוח",
    rating: 4.8,
    reviews: 240,
    sku: "BRB-PR-ST",
    voltage: null,
    origin: "איטליה",
    badge: null,
    stock: 20,
    price: 169,
    compareAt: 210,
    image:
      "https://images.unsplash.com/photo-1621607512214-68297480165e?auto=format&fit=crop&w=1000&q=80",
    blurb:
      "קצף, שמן ובלם מרענן בניחוח קלאסי. ערכה שלמה לזקן שמטופח, בלי ברק מוגזם.",
  },
  {
    id: "fast-feed",
    name: "מכונת תספורת פאסט פיד",
    brand: "Oster",
    category: "מכונות תספורת",
    rating: 4.6,
    reviews: 88,
    sku: "BRB-O-FF",
    voltage: "100–240V",
    origin: "ארה״ב",
    badge: null,
    stock: 0,
    price: 419,
    image:
      "https://images.unsplash.com/photo-1493256338651-d82f7acb2b38?auto=format&fit=crop&w=1000&q=80",
    blurb:
      "מכונת עבודה ותיקה עם מומנט גבוה. אזלה מהמלאי כרגע — אפשר לשמור אותה לרשימת המשאלות.",
  },
];

export function formatPrice(value) {
  const amount = new Intl.NumberFormat("he-IL", { maximumFractionDigits: 0 }).format(value);
  return `₪${amount}`;
}

export function findProduct(id) {
  return products.find((product) => product.id === id) ?? null;
}

export function resolveOffer(product, variantId) {
  const variant =
    product.variants?.find((item) => item.id === variantId) ||
    product.variants?.[0] ||
    null;

  if (variant) {
    return {
      variant,
      price: variant.price,
      compareAt: variant.compareAt ?? null,
      label: variant.label,
    };
  }

  return {
    variant: null,
    price: product.price,
    compareAt: product.compareAt ?? null,
    label: null,
  };
}

export function discountPercent(price, compareAt) {
  if (!compareAt || compareAt <= price) return 0;
  return Math.round((1 - price / compareAt) * 100);
}

export function fromPrice(product) {
  if (product.variants?.length) {
    return Math.min(...product.variants.map((variant) => variant.price));
  }
  return product.price;
}
